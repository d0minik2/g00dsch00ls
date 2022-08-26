<h1 align="center">g00dsch00ls</h1>


<p align="center">
    Recommendation system for secondary schools in Poland. <br> <br>
    <a href="#installation"> Installation </a> | <a href="#usage"> Usage </a>
</p> 
<br>

<h2 align="center">Installation</h2>

```console
# clone the repository
git clone https://github.com/d0minik2/g00dsch00ls.git

# change the working directory to repository directory
cd g00dsch00ls

# install the package using pip
python -m pip install -e .
```
#### or
```console
# install by pip directly from github
pip install git+https://github.com/d0minik2/g00dsch00ls.git
```


<br>

<h2 align="center">Usage</h2>


<h3 align="center">Usage with data compatible with the Polish education system</h3>

Data must have the following columns:
* subjects: list[str]
* scored_subjects: list[str]
* school_type: int
* matura_polish: float
* matura_math: float
* matura_english: float
* min_points: float
* avg_points: float

and Student information must be compatible with g00dsch00ls.PLStudent object.

Example row of data:
| profile                                                                        | school                    | school_type | address                          | subjects                                | scored_subjects                                         | min_points | avg_points | max_points | matura_polish | matura_math | matura_english |
|--------------------------------------------------------------------------------|---------------------------|-------------|----------------------------------|-----------------------------------------|---------------------------------------------------------|------------|------------|------------|---------------|-------------|----------------|
| I Liceum Ogólnokształcące - A-ogólnodostępny - matematyka, fizyka, informatyka | I Liceum Ogólnokształcące | 0           | pl. Na Groblach 9, 31-101 Kraków | ['matematyka', 'fizyka', 'informatyka'] | ['język polski', 'matematyka', 'fizyka', 'informatyka'] | 174.7      | 178.5      | 188.2      | 71.76         | 89.07       | 98.16          |

```python
import g00dsch00ls


# define the model by reading the csv file
model = g00dsch00ls.G00dSch00ls.from_csv(
    "path/to/data.csv",
    system="avg_ranking",  # define system to use (avg_ranking (default), normalization)
)

# create a student object with all the information about the student
student = g00dsch00ls.PLStudent(
    exam_results={
        "polish": 63,
        "math": 70,
        "english": 92
    },
    grades={
        "język polski": 4,
        "matematyka": 5,
        "język angielski": 5,
        # ...
    },
    liked_subjects={
        "matematyka": 1,  # value means the importance of the subject
        # ...
    },
    school_type=0,  # preferred type of school (0 - liceum, 1 - technikum, 2 - branżowa)
    additional_points=3  # points for achievements, volunteering, etc.
)

# get the first 10 recommendations for the student
recommendations = model(student, n=10)

# now you can print it or use it in your program
for i in recommendations:
    print(i)
```

<h3 align="center">Usage with your custom data</h3>

You have to write your own Student and StudentCalculator class to use your custom data.

Example row of custom data:

| name           | required_exam_result |
|----------------|----------------------|
| Example School | 55                   |

```python
import g00dsch00ls

# you can import pandas for loading your data (data must be pandas.DataFrame)
import pandas as pd


data = pd.read_csv("example_data.csv")


# write your student class, which inherits from g00dsch00ls.Student and contains your student data
class ExampleStudent(g00dsch00ls.Student):
    def __init__(
            self,
            exam_result: int,
            # ...
    ):
        self.exam_result = exam_result
        # ...


# write your student calculator class, which inherits from g00dsch00ls.StudentCalculator
# and contains methods used to compare student and profile in recommendation system
class ExampleStudentCalculator(g00dsch00ls.StudentCalculator):
    # write methods starting with "compare_", that methods will be automatically called by StudentCalculator
    def compare_exam_result(self, student: ExampleStudent, profile: pd.Series) -> float:
        # the method must take (student, profile) as arguments

        # then you can calculate the score as you wish
        if profile["required_exam_result"] < student.exam_result:
            return 0.0

        return 1.0
        # the method must return a numeric value, less means better recommendation

    # ...


student = ExampleStudent(
    exam_result=45,
    # ...
)

model = g00dsch00ls.G00dSch00ls(
    data,
    system_kwargs={
        # add your student calculator class to system_kwargs
        "student_calculator": ExampleStudentCalculator,
    }
)

# get the first 10 recommendations for the student
recommendations = model(student, n=10)

# now you can print it or use it in your program
for i in recommendations:
    print(i)
```


