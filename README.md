## COMP90024-Assignment 2-Group 46
In our study we start by looking into how road safety's influenced by factors, like traffic flow, weather conditions and pollution. We analyze datasets such as the Victorian Road Accident dataset, traffic volume information and EPA data to discover patterns and relationships that can help in reducing accidents and enhancing traffic management for urban environments. We then delve into understanding the connection between crime rates and population dynamics examining how different types of crimes align with population sizes to bolster public safety measures. Lastly we delve into Mastodon data to gauge sentiments on crime, weather conditions and car accidents. This research offers insights, for stakeholders to craft communication strategies and make well informed decisions.

### Note
If you want to test the jupyter notebook, you should pay attention to import 2 classed defined by our team.

We encapsulate some code about drawing in `pop_crime.py` and `traffic_carsh.py` to avoid redundant codes in our jupyter. 
You need to put these two files under the same directory with the `Team46_FrontEnd.ipynb`.

### Structure of Directory
* Data
  * SUDO Data - Regional Population by LGA from SUDO
  * Vic_Roads_Crash - Traffic Accidents from VIC Roads Open Data HUB
  * Vic_Traffic_Volume - Traffic Volume from VIC Roads Open Data HUB
  * Mastodon - Data from mastodon.au and mastodon.social
  * LGA_Recorded_Offences - Crime data
* Data Preprocessing
  * BOM - jupyter notebook for testing BOM transmission
  * EPA - jupyter notebook for testing EPA transmission
  * Road_Crash2ES - jupyter notebook for uploading VIC Road Crash Accidents
  * Traffic Volume - jupyter notebook for data processing and transmission
  * Mastodon - Data extraction and sentiment tests
  * Crime Analysis - jupyter notebook for testing crime data
* Frontend
  * `Team46_FrontEnd.ipynb`: The jupyter notebook shows our front end.
  * `pop_crime.py`: helper class for our front end 
  * `traffic_carsh.py`: helper class for our front end
* Fission
    * functions - fission functions that are already deployed
    * specs - YAML specifications to deploy functions
* Team Public Keypair

### Data Source
* SUDO Data: https://sudo.eresearch.unimelb.edu.au/
* Vicorian Roads Crash Data: https://vicroadsopendata-vicroadsmaps.opendata.arcgis.com/
* Traffic Volume: https://vicroadsopendata-vicroadsmaps.opendata.arcgis.com/
* Crime: https://www.crimestatistics.vic.gov.au/crime-statistics/latest-victorian-crime-data/download-data
* BOM: https://reg.bom.gov.au/vic/observations/vicall.shtml
* EPA: https://portal.api.epa.vic.gov.au/
* Mastodon:
  * Social: https://mastodon.social
  * AU: https://mastodon.au

### Dependencies
* Backend: 
  * Python3>=3.9
  * numpy==1.26.4
  * pandas==2.2.2
  * Mastodon.py==1.8.1
* Frontend: 
  * Python3>=3.10, 
  * folium==0.16.0
  * ipython==8.12.3
  * ipywidgets==8.1.2
  * matplotlib==3.8.4
  * numpy==1.26.4
  * pandas==2.2.2
  * Requests==2.32.2
  * seaborn==0.13.2
  * Shapely==2.0.4

### Vedio Demo
* Video: https://youtu.be/QKhC0zXALyI

### Team Contribution

|   Student    |   ID   |                                          Responsibility                                          |
|:------------:|:------:|:------------------------------------------------------------------------------------------------:|
| Lixinqian YU | 1420739  | VIC Roads Crash, BOM, EPA Collection, Harvester Deployment, Fission Deployment, Kafka Deployment |
| Tianhao You  | 1367258  |          VIC Roads Crash, Traffic Volume, Mastodon Data, Collection, Data Transmission           |
| Yuxin Zheng  | 1173502  |                  K8s, ES development, SUDO Data collection, Fission Deployment                   |
|  Wanxuan Wu  | 1203109 |                     Data analysis, Frontend development, Backend development                     |
| Jingxi Yuan  | 1213860 |                     Data analysis, Backend development, Frontend development                     |


