# System Design Interview: Task Processing Service

## Problem Statement

Design a web service that allows users to upload CSV files and process them asynchronously. The system should:

1. Accept CSV file uploads via a REST API / HTML Form
2. Process the files asynchronously (parsing, validation, data transformation)
3. Store processed results in a database
4. Allow users to check the status of their upload/processing jobs
5. Send email notifications when processing is complete

## Requirements

### Functional Requirements
- Users can upload CSV files (up to 10MB)
- Files are processed asynchronously (simulate 30-60 seconds processing time)
- Users receive a job ID immediately after upload
- Users can query job status using the job ID
- System stores processed data and job metadata
- Email notifications sent upon completion

### Non-Functional Requirements
- Handle up to 100 concurrent file uploads
- Process files in FIFO order
- System should be resilient to failures
- Scalable to handle growth

## Technical Constraints
- Use Django for the web framework
- Use Celery for task processing
- Use PostgreSQL for data storage
- Use Redis for caching and session storage
- Use RabbitMQ as the message broker
- Write tests (bonus)
- Deploy on Kubernetes - Use single-node self hosted option eg docker-desktop/minikube etc (bonus)


## Deliverables Expected

1. Source Code
2. Docs explaining architecture
3. Execution instructions
