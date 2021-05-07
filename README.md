# prioritized-request-handler
Implements a "fair" way to allocate resources to users requesting an intensive service.

## How to run
Clone the repo, change directory to the root of the repo and simply spin up the docker containers and you are good to go:
```
$ git clone https://github.com/moonesque/prioritized-request-handler.git

$ cd prioritized-request-handler

$ docker-compose up
```

## Now what?
There is a `Sanic` web application running in the `pqh_web` container, which exposes two endpoints:
```
POST localhost:8001/task

GET localhost:8001/result
```
You can make a `POST` request to the `/task/` endpoint in the following fashion, and submit your intensive task to the app:
```
curl --location --request POST 'localhost:8001/task' \
--header 'Content-Type: application/json' \
--data-raw '{"x": "foo", "user_id": "user_1"}'
```
The endpoint responds with such a response:
```
{
    "task_id": "f9028878-3e43-41b8-8a5d-5fe2052fd8f3",
    "result_url": "/result/f9028878-3e43-41b8-8a5d-5fe2052fd8f3",
    "user_id": "user_1"
}
```
What just happend? You provided your desired data in the body of the request in a `json` with the key "x" and value of "foo" and also your identity, key "user_id" and value "user_1". (Note that in a production scenario the identity will probably be figured out through an authentication `middleware`, but here the user provides it for the sake of simplicity.)

The API accepted your task and provided you with the `task_id` and also the `result_url`. 

If you make a `GET` request to the `/result/<task_id>/` endpoint:
```
curl --location --request GET 'localhost:8000/result/f9028878-3e43-41b8-8a5d-5fe2052fd8f3'
```
or simply follow the `result_url`, you can find out about the result of your submitted task. 

If the task is already done, the endpoint responds with such a response:

```
{
    "task_id": "f9028878-3e43-41b8-8a5d-5fe2052fd8f3",
    "task_status": "SUCCESS",
    "task_result": {
        "init_timestamp": 1620388295.0721116,
        "input_x": "foo",
        "done_timestamp": 1620388296.0739212
    }
}
```
If not done yet:
```
{
    "task_id": "f9028878-3e43-41b8-8a5d-5fe2052fd8f3",
    "task_status": "PENDING",
    "task_result": null
}
```

You can check again and hopefully the result will be ready by then.


## What is happening behind the scenes?
The intensive task is running the function `limited_f(x)` for the user, which simply "sleeps" for 60 seconds. 
We certainly don't want the user who sent the request to wait 60 seconds for the `HTTP` response, so we utilize a task queue to handle the task asynchronously, and respond to the request right away with the task id.

`Celery` is used as the task queue and `redis` as its message broker.

## How is the service fairly allocated to users?
We dont want users to hog our limited service with their non stop requests, so we need to prioritize some requests over others. For that matter, we need to keep track of the number of requests each user made in some specific time period up until now.

In the current configuration of the project, every time a user submits a tasks (makes a requests), a `redis` key (with their `user_id`, e.g user_2) is updated(incremented). The current value of this key determines the priority that their task will have to the `Celery` worker, the higher the value, the lower the priority. Note that the key has a configurable `TTL`, which allows the records of the users to be cleaned if they stop hogging the service.

## All the details...
The priority system consists of 6 levels:

|Level  |Current number of submitted tasks in the last T seconds|
|:----: |:-----------------------------------------------------:|
|0      |`0`                                                      |
|1      |`[1, 5] `                                                |
|2      |`[6, 15]`                                                |
|3      |`[16, 25]`                                               |
|4      |`[26, 35]`                                               |
|5      | `>= 36`                                                 |


The level 0 has the highest priority and belongs to users who are submitting their first task. These users will have the result of their task ready first, followed by the users who have submitted up to 5 tasks in the last T seconds(level 1), and so on.

Making use of the priority feature of the `Celery` task queue, these levels will map to respective queues that the worker will consume from according to the respective order of priority.

## Adding weight to the mix...
An idea for weighted user priority could be assigning a weight integer to each user and __dividing their submitted task number by the weight__. 
For instance, a user with the weight of 6, having submitted 5 tasks recently, could still use the level 0 priority queue, since
```
5 // 6 = 0
```

## Testing it out...
The `pqh_dashboard` hosts a `flower` dashboard monitoring `Celery`. It can be used to keep track of the tasks.
