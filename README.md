# Energy Planning Application

Energy Planning Application (EPA) is a web application providing a user interface for simulation and evaluation of DER investment case studies in sector-coupled energy systems.
It is developed by [Intracom Telecom](http://www.intracom-telecom.com/) under the umbrella of the H2020 project [E-LAND](https://elandh2020.eu/) (Integrated multi-vector management system for Energy isLANDs, Grant Agreement 824388).

The EPA utilizes as its simulation engine the Multi-Vector Simulator ([MVS](https://github.com/rl-institut/multi-vector-simulator)) developed (under E-LAND project as well) by Reiner Lemoine Insitut (RLI). Hence it inherits the grid modelling and simulation features and constraints of the MVS. Neverthenless, the EPA is developed and maintained independently hence some features of the MVS might not be yet available in EPA.

The solution is licensed under MIT license.

##Features
The main features of the EPA are:
- Modelling multiple investment projects per user
- Multiple case studies (scenarios) for each project
- Drag and drop tool for modelling the energy system
- Analysis of an energy system model and optimisation of generation and storage assets (through MVS)
- Multiple user support
- Share project with another user (read-only)
- Basic user authentication

##Dependencies
The main technologies based on which EPA is developed are the following:
- [Django](https://www.djangoproject.com/) as the core web framework;
- [MySQL](https://www.mysql.com/) v5.7 as Database Management System (DBMS);
- Bootstrap 3, JQuery, [Drawflow](https://github.com/jerosoler/Drawflow), Selectize, PlotlyJS and JQuery-UI are the major JavaScript libraries
- [Nginx](https://www.nginx.com/) as a reverse proxy and load balancer.
- [Django-q](https://github.com/Koed00/django-q) as task manager;

The EPA is packaged using [Docker](https://github.com/docker), hence all the required dependencies and configurations are included.
It can be instantiated in different ways:
- Using MVS's web API [deployed from RLI](https://mvs-eland.rl-institut.de/)
- Via locally installing the latest stable MVS API project from the relevant [repo](https://github.com/rl-institut/mvs_eland_api.git)

#Getting Started

## Deploy using Docker Compose - use of MVS web API
The following commands should get everything up and running, utilzing the web based version of the MVS API.
1. `git clone --single-branch --branch main https://github.com/isichos/epa.git`
2. cd inside the created folder
4. `docker-compose up -d --build`
5. `docker-compose exec app sh setup.sh` (this will also load a default testUser account with sample scenario).
6. Open browser and navigate to http://localhost:80.

>**_NOTE:_** If you use a proxy you will need to introduce modifications to app/epa.env to fit your needs.
<hr>

## Deploy using Docker Compose - use of MVS locally
The following commands should get everything up and running, using a local copy of MVS API.
You can either use the existing `mvs_eland_api` folder or clone the latest stable version of the MVS API with `git clone --single-branch --branch epa_stable https://github.com/rl-institut/mvs_eland_api.git`

1. `git clone --single-branch --branch main https://github.com/isichos/epa.git`
2. cd inside the created folder
4. `git clone --single-branch --branch epa_stable https://github.com/rl-institut/mvs_eland_api.git` to clone the latest stable MVS API version.
5. `docker-compose -f docker-compose_with_mvs.yml up -d --build`
6. `docker-compose exec app sh setup.sh` (this will also load a default testUser account with sample scenario).
7. Open browser and navigate to http://localhost:80.

>**_NOTE:_** Grab a cup of coffee or tea for this...
<hr>

## Test Account
> You can access a preconfigured project using the following login credentials:  `testUser:ASas12,.`
<hr>

## Tear down
> To remove the application (including relevant images, volumes etc.), one can use the following commands in cmd:
- `docker-compose down --volumes --rmi local`, or
- `docker-compose -f docker-compose_with_mvs.yml down --volumes --rmi local` if docker-compose_with_mvs.yml configuration was utilized.
<hr>

## Installation Notes
1. Docker engine should be started to run the application
2. An error might occur on `setup.sh` execution. This is because of the underlying OS and the way it handles EOL. Try to execute the commands in the file sequentially instead.
