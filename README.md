# Team Ibis Small Group project

## Team members
The members of the team are:
- Jacelyne Tan
- Aravinth Kaneshalingam
- Natalia Ahsan
- Emil Khojayev
- Jasmin Bedi

## Project structure
The project is called `task_manager`.  It currently consists of a single app `tasks`.

## Deployed version of the application
The deployed version of the application can be found at https://jacelyne.pythonanywhere.com/.

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  From the root of the project:

```
$ virtualenv venv
$ source venv/bin/activate
```

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Migrate the database:

```
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Run all tests with:
```
$ python3 manage.py test
```

*The above instructions should work in your version of the application.  If there are deviations, declare those here in bold.  Otherwise, remove this line.*

## Sources
The packages used by this application are specified in `requirements.txt`

Usage of AI - Aravinth Kaneshalingam

To ensure maximum code coverage, I utilised ChatGPT to assist in writing tests for branches and statements that were missing in the following test files:
- test_student_request_processing_view.py
- test_lesson_update_view.py
- test_lesson_model.py

I also used ChatGPT for a few tips when refactoring the code the wrote that I wrote, which helped me cut down my code length and ensure that each method and class I created was small and each focused on a single responsibility/task. ChatGPT was utilised in this sense for the following classes:
- LessonUpdateForm - forms.py
- StudentRequestProcessingView - views.py

Leveraging ChatGPT has also significantly increased my understanding of writing and debugging tests as well as identifying logical errors, which has ensured that the functionality I was responsible for is well-tested.

I also used W3Schools (https://www.w3schools.com/html/default.asp) in order to learn HTML which was extremely helpful when creating the templates I was responsible for.
