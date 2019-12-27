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