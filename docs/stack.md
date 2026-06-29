# Desired tech stack (planning)

This is intentionally slim and will be deleted later. Just filling in as reading through the specs.

## Backend Logic

Per specs, we will be using **python** with **django** framework. This will interact directly with the frontend via Django templates, which will make it a bit easier.

## Database

Given the basic CRUD operations, a local Postgresql database will be used. This ensures extensibility if we would want to migrate to cloud services, such as AWS or GCP, while still providing some of the more advanced features.

## Frontend

Since we will be using standard HTML with django templating, we will use tailwind as the ui library for a easy user interface.
