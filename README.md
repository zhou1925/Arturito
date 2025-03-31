# Arturito Bot
Arturito is a bot wiht generative AI that can assist you with his tools
His name is inspired by R2-D2, known as Arturito in Latin-America, it is a fictional robot from the Star Wars.
The pronounciation in spanish sounds like: “ar-tu-di-tu”. So that is the origin of his name.

# Purpose
- Use todoist tasks to assit you or improve your performance
- help with common tasks like web search, pdf creation, slides creation
- 

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

- [ ] implement todoist service
    - [ ] def create_project(self): pass
    - [ ] def create_section(self): pass
    - [ ] def get_task_comments(self): pass
- [ ] implement google docs reader service
- [ ] implement google sheets reader service
- [ ] implement gemini service
- [ ] implement cloudinary service (handle files)
- [ ] 


## CURRENT FEATURES
- [ ] 


## FUTURE FEATURES
- [ ] LONG MEMORY
- [ ] MULTI TASK
- [ ] 


### Running tests

```
pytest -v
```