from pathlib import Path
import subprocess


def check_examples() -> None:
    """
    This function is used to run all the examples in the CI to ensure that they work,
    it is not meant to be used locally or as an example.
    """
    examples_folder = Path(__file__).parent

    example_files = [
        file
        for file in examples_folder.iterdir()
        if file.suffix == ".py" and str(file) != __file__ and file.name != "__init__.py"
    ]

    for example_file in example_files:
        print(f"Running example {str(example_file)}")
        subprocess.call(["python", str(example_file)], stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    check_examples()
