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


~~~
> Minikube start --cpus 8 --memory 8192
> 
~~~

##### HTTP 에코 서버 deployment 

deployment를 구동하기 위해 first-deployment.yaml 코드를 작성함.
> 이미지는 k8s 에서 제공하는 http echo server (k8s.gcr.io/echoserver:1.10) 을 사용.

~~~
> kubectl create deployment -f first.deployment.yaml
deployment.apps/first-deployment created
>kubectl get pod
NAME                                READY   STATUS    RESTARTS   AGE
first-deployment-6fbc68f797-9dfrz   1/1     Running   0          17s
first-deployment-6fbc68f797-fs2fz   1/1     Running   0          17s
first-deployment-6fbc68f797-wf4st   1/1     Running   0          17s
~~~

##### pod에 연결하기 위한 service 배포

pod를 외부에서 보기 위해 first-service.yaml 을 작성함.

~~~
> kubectl create -f first-service.yaml
service/hello-service created
> kubectl get svc
C:\Users\lsn31\Documents\kube_tutorial-sun>kubectl get svc
NAME            TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
hello-service   LoadBalancer   10.96.166.133   <pending>     80:32215/TCP   6s
kubernetes      ClusterIP      10.96.0.1       <none>        443/TCP        38m

~~~

