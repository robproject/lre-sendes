### Description
This application allows for the operation, configuration management, data logging, and plotting of results from a Labjack T7, as configured for LRE's Senior Design project through CSULB AVEP. 

[Video](https://youtu.be/FuWRMdm6EqA)
### Local Setup
Assuming python3 is already installed:
```
git clone https://robproject/lre-sendes
cd lre-sendes
pip install -r sendes/requirements.txt
export FLASK_APP=sendes/app FLASK_ENV=development FLASK_DEBUG=1 SECRET_KEY=my_key
flask run
``````
