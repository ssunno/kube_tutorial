#### kubernetes tutorial

Kubernetes 연습 기록.

------
##### 환경

연습용이므로 로컬 환경에서 작업한다.
* OS : MacOS Catalina 10.15.2

##### Docker for Mac 설치 & Kubernetes 설정

Docker for Mac에서 Kubernetes 사용을 지원하므로 이를 사용해서 환경을 구성함.

설치한 버전:
* Docker desktop 2.1.0.4
* Docker Engine 19.03.4
* Kubernetes v1.14.7

------

#### 3주차 기록

Kubernetes API를 사용하기 위한 언어로 파이썬을 사용했다.

~~~ python
# Python에서 k8s API를 사용하기 위한 패키지 설치
> pip install kubernetes
Collecting kubernetes
  Downloading https://files.pythonhosted.org/packages/6e/fc/2cab119f679648b348b8940de0dd744a1f0ee99c690aa2ef6072f050816c/kubernetes-10.0.1-py2.py3-none-any.whl (1.5MB)
    100% |████████████████████████████████| 1.5MB 7.8MB/s
...
Successfully installed cachetools-4.0.0 google-auth-1.10.1 kubernetes-10.0.1 oauthlib-3.1.0 pyasn1-0.4.8 pyasn1-modules-0.2.8 requests-oauthlib-1.3.0 rsa-4.0 urllib3-1.25.7 websocket-client-0.57.0
~~~

Python에서 k8s API를 사용해서 접근하려면 먼저 *kubeconfig*를 사용해 k8s 클러스터와 연결해야 한다.

> 실험 환경인 Docker for Mac 의 k8s 환경은 로컬에 설치되기 때문에, API 사용시 kubeconfig를 따로 지정하지 않으면 $HOME/.kube/config 를 기본으로 사용해서 로컬에 접속 할 수 있다.

*kubeconfig* 는 k8s 클러스터 접근을 위한 정보(certificate auth data, cluster context, user context 등) 들을 가지고 있다. *kubectl config view* 명령어로 현재 연결된 *kubeconfig*를 확인 할 수 있다. 여러 개의 *kubconfig*를 가지고 있으면 context를 변경해서 여러 클러스터에 접근 할 수도 있다.

~~~ shell
> kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://kubernetes.docker.internal:6443
  name: docker-desktop
contexts:
...
~~~

> $HOME/.kube/config 에서 config 실제 config 인증 키와 같은 정보들을 가지고 있다.

**Python kubernetes client API** 에서는 *{k8s client API}.config.load_kube_config()* 메서드로 config file을 선택하거나 context를 직접 지정할 수 있다. 매개변수로 아무것도 입력하지 않으면 kubctl 에서 설정된 context를 기본으로 사용한다.

* Pod 리스트를 얻어오는 기능은 *{k8s client API}.CoreV1Api.list_pod_for_all_namespaces()* 메서드를 사용한다.
* k8s 상태를 모니터링 하는 기능으로는 *{k8s client API}.watch.Watch()* 를 사용해서 pod의 list 상태를 지속적으로 감시할 수 있다.

~~~ Python
######## python 코드(pods_watcher.py) ########
import kubernetes as k8s
# get kubernetes config.
k8s.config.load_kube_config()

def watch_pods(timeout=120):
    """Notice when pod created & deleted

    Keyword Arguments:
        timeout {int} -- how long watch k8s status (default: {120})
    """
    # dictionary of type-message pair
    watch_type = {'ADDED': 'Hello',
                  'DELETED': 'Good bye'}
    api = k8s.client.CoreV1Api()
    watcher = k8s.watch.Watch()
    stream = watcher.stream(api.list_pod_for_all_namespaces, timeout_seconds=timeout)
    for raw_event in stream:
        if raw_event['type'] in watch_type.keys():
            print('%s, %s' % (watch_type[raw_event['type']], raw_event['object'].metadata.name))
~~~

Pod리스트를 가져오는 기능을 감시하고 있으면 Pod 상태가 변화할 때 마다 stream 으로 알려준다.

##### 동작 확인

현재 pod 상태는 1주차에 생성한 *first-deployment* 가 3개의 Pod를 유지하고 있는 상태.

~~~ shell
> kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
first-deployment-fbf887d8-9bv8b   1/1     Running   0          40h
first-deployment-fbf887d8-hc7lf   1/1     Running   0          40h
first-deployment-fbf887d8-pgc8t   1/1     Running   0          16h
shell-demo                        1/1     Running   1          14d
~~~

*pods_watcher.py* 를 실행해서 k8s 상태를 모니터링 한다.
~~~ shell
> python3 pods_watcher.py
Hello, etcd-docker-desktop
Hello, kube-scheduler-docker-desktop
Hello, compose-api-57ff65b8c7-drzbz
Hello, coredns-6dcc67dcbc-g9s2b
Hello, coredns-6dcc67dcbc-zmkm7
Hello, compose-6c67d745f6-9vjx6
Hello, kube-apiserver-docker-desktop
Hello, kube-proxy-gmljx
Hello, first-deployment-fbf887d8-9bv8b
Hello, first-deployment-fbf887d8-pgc8t
Hello, shell-demo
Hello, kube-controller-manager-docker-desktop
Hello, first-deployment-fbf887d8-hc7lf
~~~

생성된 3개의 Pod 중 하나(*first-deployment-fbf887d8-9bv8b*)를 삭제하면, pods_watcher에 삭제 이벤트가 기록된다.
~~~ shell
...
Hello, kube-controller-manager-docker-desktop
Hello, first-deployment-fbf887d8-hc7lf
Hello, first-deployment-fbf887d8-nbtml
Good bye, first-deployment-fbf887d8-9bv8b
~~~

> 이 때 새로운 Pod(first-deployment-fbf887d8-nbtml)가 생성되는 것은 first-deployment가 3개의 Pod를 유지시키려고 하기 때문에 kubectl로 삭제한 Pod를 대신해서 새 Pod를 띄운 것이다.

deployment에서 replica를 조정하는 예시(replicas: 3 -> 1):
~~~ yaml
# first-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: first-deployment
spec:
  replicas: 1
  ...
~~~

~~~ shell
> kubectl apply -f first-deployment.yaml
deployment.apps/first-deployment configured

// in pods_watcher.py
...
Good bye, first-deployment-fbf887d8-nbtml
Good bye, first-deployment-fbf887d8-pgc8t
~~~


------

#### 2주차 기록

##### Service 타입 변경

이전 주차에서 Service 생성시 사용한 LoadBalancer는 다양한 kubernetes 외부 밸런서가 존재한다.

> 1주차에서 LoadBalancer는 Docker for Mac에 내장된 nginx가 아닐지 싶다.

이를 kubernetes 기본 제공인 ClusterIP로 변경하기:

* ~~type: LoadBalancer~~
* type: ClusterIP

ClusterIP는 kubernetes 클러스터 내에서 다른 서비스들이 접근할 수 있게 내부 IP를 할당하기 때문에 k8s클러스터 외부에서는 접근할 수 없다.

기존에 LoadBalancer 타입으로 만든 서비스를 삭제하고 ClusterIP 타입으로 만든 서비스를 다시 올림.
~~~
> kubectl delete service hello-service
service "hello-service" deleted

> kubectl get svc
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   6d

> kubectl create -f first-service.yaml
service/hello-service created
> kubectl get svc
NAME            TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
hello-service   ClusterIP   10.98.247.37   <none>        80/TCP    5s
kubernetes      ClusterIP   10.96.0.1      <none>        443/TCP   6d
~~~

##### LoadBalancer 조사

로드밸런서는 서비스를 외부로 노출시키는 방법 중 하나이다. 로드밸런서는 IP주소를 제공하고 지정된 포트로 들어오는 모든 트래픽을 Service로 포워딩 해 주는 역할을 한다. 주로 클라우드 벤더(구글 등)에서 제공하는 load balancer를 사용하며 이 때는 비용이 부과될 수 있음.

Host based Load Balancer는 Ingress 컴포넌트에서 HTTP 주소 기반 L7 로드밸런싱을 지원한다. Ingress는 여러 서비스 앞에서 라우터로써 다양한 기능을 제공할 수 있다. ex)Google, Amazon 등에서 제공하는 로드밸런서는 Ingress 형태로 경로 기반 라우팅과 서브도메인 기반 라우팅을 모두 지원한다.

Ingress 설정은 컴포넌트 타입을 Ingress로 정의하고 Path 또는 subdomain 기반으로 라우팅할 서비스 정보를 넣어서 생성하면 된다. Ingress는 L7 이므로 SSL, Auth 같은 기능을 추가로 제공 할 수도 있다.


##### Service 개념 정리

1주차에 생성한 Service는 first-deployment에 의해 관리되는 3개의 Pod에 대한 라우팅을 담당함. Service에서 보이는 Endpoint는 3개로 각 Pod가 쿠버네티스 클러스터 내에서 부여받는 내부 주소이다.

~~~
> kubectl describe service hello-service
Name:              hello-service
Namespace:         default
Labels:            <none>
Annotations:       <none>
Selector:          app=hello-deploy
Type:              ClusterIP
IP:                10.98.247.37
Port:              http  80/TCP
TargetPort:        8080/TCP
Endpoints:         10.1.0.20:8080,10.1.0.21:8080,10.1.0.22:8080
Session Affinity:  None
Events:            <none>
~~~

ClusterIP 타입이므로 k8s 클러스터 외부에서 해당 서비스로 접근할 수는 없다. 임시로 내부 네트워크에서 접근을 테스트하기 위해 pod를 하나 생성하고 bash로 ClusterIP에 요청을 테스트 했다:

~~~
> kubectl apply -f https://k8s.io/examples/application/shell-demo.yaml

pod/shell-demo created
> kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
first-deployment-fbf887d8-j44hj   1/1     Running   2          7d
first-deployment-fbf887d8-q687v   1/1     Running   2          7d
first-deployment-fbf887d8-vjjkj   1/1     Running   2          7d
shell-demo                        1/1     Running   0          18s

> kubectl exec -it shell-demo -- /bin/bash
...
root@docker-desktop:/# curl 10.98.247.37
Request served by first-deployment-fbf887d8-vjjkj

HTTP/1.1 GET /

Host: 10.98.247.37
User-Agent: curl/7.64.0
Accept: */*

root@docker-desktop:/# curl 10.98.247.37
Request served by first-deployment-fbf887d8-j44hj

HTTP/1.1 GET /

Host: 10.98.247.37
User-Agent: curl/7.64.0
Accept: */*
~~~

shell-demo Pod를 통해 접근시 Pod에 접근이 가능하다. Endpoint는 Pod가 노드 내에서 임시로 부여받는 주소이므로 endpoint 주소로 curl 명령을 보내도 동작한다:

~~~
root@docker-desktop:/# curl 10.1.0.20:8080
Request served by first-deployment-fbf887d8-vjjkj

HTTP/1.1 GET /

Host: 10.1.0.20:8080
User-Agent: curl/7.64.0
Accept: */*

root@docker-desktop:/# curl 10.1.0.21:8080
Request served by first-deployment-fbf887d8-j44hj

HTTP/1.1 GET /

Host: 10.1.0.21:8080
User-Agent: curl/7.64.0
Accept: */*

root@docker-desktop:/# curl 10.1.0.22:8080
Request served by first-deployment-fbf887d8-q687v

HTTP/1.1 GET /

Host: 10.1.0.22:8080
User-Agent: curl/7.64.0
Accept: */*
~~~

하지만 Endpoint는 pod가 재시작 된다거나 할 때 바뀔 수 있으므로 Endpoint 주소를 외부에서 사용하는 것은 바람직하지 않다. Service는 이같은 경우에서 연결된 Pod들의 Endpoint를 관리하고 여러개로 띄워진 Pod에 단일 IP를 제공하게 된다.


##### 쿠버네티스 클러스터 내부에서 curl 10.98.247.37 요청시 흐름

1. docker-desktop 내 shell-demo 에서 curl 요청
2. shell-demo 가상 이더넷 컨트롤러에서 10.98.247.37 정보를 모르기 때문에 상위 이더넷 컨트롤러(docker-desktop node 컨트롤러)로 전달.
3. 10.98.247.37(hello-service)가 노드(docker-desktop) 상에 있으므로 hello-service로 요청을 전달
4. hello-service가 연결된 3개의 Pod 중 하나를 선택하고 선택한 Pod의 Endpoint 주소로 요청을 전달
5. Endpoint 주소에 해당하는 Pod에서 echo-server 동작 실행

> kube-proxy는 노드마다 존재하는 proxy로, 노드 내로 라우팅 되어야 하는 패킷을 iptables 로 관리하고 업데이트 하는 일을 한다고 함. 자세한 동작은 더 알아봐야 겠으나 이 경우 실제로는 shell-demo 에서 echo-server Pod로 바로 전달되는 것 같기도 함.

##### L7 Load Balancer가 포함된 curl 요청 흐름

1. **k8s cluster 외부**에서 Load Balancer의 domain주소로 curl 요청 -- LoadBalancer가 host 주소를 가지고 있어야 한다.
2. LoadBalancer 내에서 사전 정의된 path(or subdomain)과 Service 매핑 규칙에 따라 트래픽을 해당 Service(hello-service)로 포워딩
3. hello-service가 연결된 3개의 Pod 중 하나를 선택하고 선택한 Pod의 Endpoint 주소로 요청을 전달
4. Endpoint 주소에 해당하는 Pod에서 echo-server 동작 실행

> 클러스터 내부에서 접근할 때와 다른점은 2번으로, 외부 요청에 대해 사전정의한 규칙대로 Service를 매핑한다. 이 LoadBalancer를 정의할 때 service의 clusterIP를 지정할 필요는 없고 ServiceName과 clusterIP의 port를 작성한다.

> Google Cloud의 LoadBalancer를 사용할 때는 서비스를 NodePort 타입으로 지정한다. NodePort는 모든 노드의 특정 포트가 하나의 서비스로 연결되는 방식이다. 어떤 노드에서건 해당 nodePort로 연결을 시도하면 지정된 서비스로 포워딩 된다고 한다.

------

#### 1주차 기록

##### HTTP 에코 서버 deployment

deployment를 구동하기 위해 first-deployment.yaml 코드를 작성함.
> 이미지는 k8s 에서 제공하는 http echo server (k8s.gcr.io/echoserver:1.10) 을 사용.

~~~
> kubectl create deployment -f first.deployment.yaml
deployment.apps/first-deployment created
>kubectl get pods
NAME                                READY   STATUS              RESTARTS   AGE
first-deployment-58b54db964-jh65s   0/1     ContainerCreating   0          13s
first-deployment-58b54db964-mk72h   0/1     ContainerCreating   0          13s
first-deployment-58b54db964-r2n8n   1/1     Running             0          13s
~~~

##### pod에 연결하기 위한 service 배포

pod를 외부에서 보기 위해 first-service.yaml 을 작성함.

~~~
> kubectl create -f first-service.yaml
service/hello-service created
> kubectl get svc
NAME            TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
hello-service   LoadBalancer   10.105.176.255   localhost     80:30794/TCP   5s
kubernetes      ClusterIP      10.96.0.1        <none>        443/TCP        12m
~~~

연결 테스트로 방금 만든 서비스로 http 요청 전송:

~~~
> curl localhost


Hostname: first-deployment-58b54db964-r2n8n

Pod Information:
        -no pod information available-

Server values:
        server_version=nginx: 1.13.3 - lua: 10008

Request Information:
        client_address=192.168.65.3
        method=GET
        real path=/
        query=
        request_version=1.1
        request_scheme=http
        request_uri=http://localhost:8080/

Request Headers:
        accept=*/*
        host=localhost
        user-agent=curl/7.63.0

Request Body:
        -no body in request-

> curl localhost


Hostname: first-deployment-58b54db964-mk72h
...
~~~

##### 롤링 업데이트 테스트

HTTP echo server 이미지를 다른 것으로 교체하기 위해 first-deploy.yaml 파일에서 image를 다른 것으로 수정함.
* ~~image: k8s.gcr.io/echoserver:1.10~~
* image: jmalloc/echo-server:latest

수정한 deployment 스크립트를 적용하고 포드가 롤링 업데이트 되는 것 확인:

~~~
> kubectl replace -f first-deployment.yaml
deployment.apps/first-deployment replaced

> kubectl get pods
NAME                                READY   STATUS    RESTARTS   AGE
first-deployment-58b54db964-jh65s   1/1     Running   0          11m
first-deployment-58b54db964-mk72h   1/1     Running   0          11m
first-deployment-58b54db964-r2n8n   1/1     Running   0          11m
first-deployment-fbf887d8-j44hj     1/1     Running   0          12s

> kubectl get pods
NAME                                READY   STATUS              RESTARTS   AGE
first-deployment-58b54db964-jh65s   1/1     Running             0          11m
first-deployment-58b54db964-mk72h   1/1     Terminating         0          11m
first-deployment-58b54db964-r2n8n   1/1     Running             0          11m
first-deployment-fbf887d8-j44hj     1/1     Running             0          15s
first-deployment-fbf887d8-vjjkj     0/1     ContainerCreating   0          2s

> kubectl get pods
NAME                                READY   STATUS        RESTARTS   AGE
first-deployment-58b54db964-jh65s   1/1     Running       0          11m
first-deployment-58b54db964-mk72h   1/1     Terminating   0          11m
first-deployment-58b54db964-r2n8n   1/1     Running       0          11m
first-deployment-fbf887d8-j44hj     1/1     Running       0          19s
first-deployment-fbf887d8-vjjkj     1/1     Running       0          6s

> kubectl get pods
NAME                                READY   STATUS        RESTARTS   AGE
first-deployment-58b54db964-jh65s   1/1     Terminating   0          11m
first-deployment-58b54db964-mk72h   1/1     Terminating   0          11m
first-deployment-58b54db964-r2n8n   1/1     Running       0          11m
first-deployment-fbf887d8-j44hj     1/1     Running       0          29s
first-deployment-fbf887d8-q687v     1/1     Running       0          5s
first-deployment-fbf887d8-vjjkj     1/1     Running       0          16s

...

> kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
first-deployment-fbf887d8-j44hj   1/1     Running   0          3m52s
first-deployment-fbf887d8-q687v   1/1     Running   0          3m28s
first-deployment-fbf887d8-vjjkj   1/1     Running   0          3m39s
~~~

describe 명령어로 deployment가 수행한 작업 내역을 확인함:

~~~
> kubectl describe deploy first-deployment
Name:                   first-deployment
Namespace:              default
CreationTimestamp:      Fri, 27 Dec 2019 22:56:39 +0900
Labels:                 <none>
Annotations:            deployment.kubernetes.io/revision: 2
Selector:               app=hello-deploy
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        5
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=hello-deploy
  Containers:
   hello-deploy:
    Image:        jmalloc/echo-server:latest
    Port:         8080/TCP
    Host Port:    0/TCP
    Environment:  <none>
    Mounts:       <none>
  Volumes:        <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   first-deployment-fbf887d8 (3/3 replicas created)
Events:
  Type    Reason             Age    From                   Message
  ----    ------             ----   ----                   -------
  Normal  ScalingReplicaSet  16m    deployment-controller  Scaled up replica set first-deployment-58b54db964 to 3
  Normal  ScalingReplicaSet  4m40s  deployment-controller  Scaled up replica set first-deployment-fbf887d8 to 1
  Normal  ScalingReplicaSet  4m27s  deployment-controller  Scaled down replica set first-deployment-58b54db964 to 2
  Normal  ScalingReplicaSet  4m27s  deployment-controller  Scaled up replica set first-deployment-fbf887d8 to 2
  Normal  ScalingReplicaSet  4m17s  deployment-controller  Scaled down replica set first-deployment-58b54db964 to 1
  Normal  ScalingReplicaSet  4m16s  deployment-controller  Scaled up replica set first-deployment-fbf887d8 to 3
  Normal  ScalingReplicaSet  4m6s   deployment-controller  Scaled down replica set first-deployment-58b54db964 to 0
~~~

curl 명령어를 사용하면 echo server 이미지가 바뀌었기 때문에 이전과 다른 형태로 응답이 오는 것을 확인 함:

~~~
> curl localhost
Request served by first-deployment-fbf887d8-j44hj

HTTP/1.1 GET /

Host: localhost
User-Agent: curl/7.63.0
Accept: */*
~~~



------

##### Note
* Minikube를 사용하려고 했으나 service 등록 부분에서 loadBalancer 문제로 진행이 안됐음.
* Windows 10 환경에서는 진행에 문제가 있어 포기함. (도커가 win10 Pro 부터 제대로 지원)
* 클라우드 환경 에서도 시도 해 볼 예정



