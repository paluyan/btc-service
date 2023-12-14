# btc-service
Microservice to retrieve the current price of bitcoin 


Endpoints:
/current_price
/average_daily
/monthly_averages

Secrets to  to leverage the microservice will be created directly in k8s cluster or with a helm and credentials than will be stored on Jenkins.
I deployed it on internal k8s cluster, everything is work, but I can`t get an external ip to make it public for you. 
In that case you can make : curl -u user:pass  http://NodeIP:NodePort/endpoint
