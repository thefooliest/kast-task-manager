## Architectural decisions
### keep separeted DB model from bussiness logic
It is a common practice to define bussiness models using SQLAlchemy declarative base.  

Although SQLAlchemy declarative base has synergy with Alembic migrations, it introduces coupling between database and bussiness logic, it also makes backend dependant on SQLAlchemy. As consequence, if domain modifications are needed, developer will be forced to modify database too and DB modifications force to change bussiness models or even services. 

To avoid those problems, I decided to use ORM models and domain models separatedly. The relationship between them is created using a repository class, then, repository is injected in service, allowing to change for another repository if needed.

## Trade-offs I considered

## What I prioritized and why

## What I would improve with more time

## How to run and test