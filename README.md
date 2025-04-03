# Arturito Bot with TODOIST 
Arturito is a bot wiht generative AI that can assist you with his tools. the comunication is fetching tasks from TODOIST. identify actions and execute them.
His name is inspired by R2-D2, known as Arturito in Latin-America, it is a fictional robot from the Star Wars.
The pronounciation in spanish sounds like: “ar-tu-di-tu”. So that is the origin of his name.

# Purpose
- Use todoist tasks to assit you or improve your performance
- help with common tasks like web search, pdf creation, slides creation, etc
- 

## WHY?
- I am lazy so i become productive doing something can improve my laziness

## What can do?
- Connect with your Todoist API and fetch all tasks assigned to him by example tag: @arturito
- labels from todoist are used for actions
- You receive feedback in your todoist Task by comments or Task update: content, description, labels, etc
- In future can work as a co-assitant where can plan, create tasks, assign etc.


## How it Works?
- you program your tools to do a specific thing by example: web search, create pdf, etc
- you can use services module to setup external API integrations
- 

# MAIN ARCHITECTURE

## TASKS
- tasks are used for Arturito,
- a task can see as:
    - Title = Goal
    - content = Goal description
    - labels = Actions

## SERVICES
Services are in charge of work with external services, connect with any service you are want.
in this particular case:
- Todoist API
- SERPER API
- Cloudinary API

## TOOLS
Tools is where you will put your custom class of your tool to create any by your preference.

## Actions

# TODO

- [X] implement todoist service
- [X] implement google docs reader service
- [X] implement google sheets reader service
- [X] implement gemini service
- [X] implement cloudinary service (handle files)
- [X] implement agent
- [X] implement orchestrator
- [ ] refactor?


## FUTURE FEATURES
- [ ] LONG MEMORY
- [ ] MULTI TASK
- [ ] Workflows


### Running tests

```
pytest -v
```

# PROBLEMS
hmmm i think is a bit messy when i want to add a tool, inject the tool and service...
i need a way to properly this works but more simplier. even myself i got lost when i need to add a new service and tool in this case the doc summarizer.

- Prompts can be isolated i think ( maybe a yml file to write the instrucions or workflow?)

## TOOLS
[there is a problem in tools... i think]
tools execute and we are not isolating the actions.

## SERVICES
- services are good i think,

## RUTINES
- we need to isolate our rutines for our agent

## AGENT
- is in charge of a lot of responsabilities... this guy needs be refactor