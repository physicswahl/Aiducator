# Syllabus Reader Project

This Django project is designed to read a PDF of a school syllabus, organize the information, and display it on a website. 

## Project Structure

```
syllabus_reader/
├── manage.py
├── README.md
├── requirements.txt
├── syllabus_reader/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── syllabus/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── syllabus/
│           └── syllabus_display.html
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd syllabus_reader
   ```

2. **Create a virtual environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages**:
   ```
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```
   python manage.py migrate
   ```

5. **Run the development server**:
   ```
   python manage.py runserver
   ```

## Usage

- Upload a PDF syllabus through the designated view (to be implemented).
- The application will process the PDF and extract relevant information.
- Access the organized syllabus information at the specified URL.

## Requirements

- Python 3.x
- Django
- Libraries for PDF processing (e.g., PyPDF2, pdfminer.six)

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.