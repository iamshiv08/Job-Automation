
# 🤖 Job Automation

**Job Automation** is a Streamlit-based web app that scrapes job listings from [Naukri.com](https://www.naukri.com) using **Selenium**.
It allows you to search for IT jobs by title and city, preview results in a table, and download them in **CSV** or **PDF** format.

---

## ✨ Features

* 🔍 Search jobs by title and city
* ⚡ Scrape up to 50 job listings at a time
* 📊 Live progress updates during scraping
* 🗂 Preview job data in an interactive table
* 📥 Export results to **CSV** and **PDF**
* 📌 Saves details like title, company, salary, location, description, skills, and link

---

## 📦 Requirements

* **Python 3.8+**
* [Google Chrome](https://www.google.com/chrome/)
* [ChromeDriver](https://chromedriver.chromium.org/downloads) (must match your Chrome version)
* Packages (install via pip):

  ```sh
  pip install streamlit selenium beautifulsoup4 fpdf
  ```

---

## ⚠️ Important Note

Before running the app, download **ChromeDriver** and update the path inside the code:

```python
chrome_driver_path = r"C:\Users\your-system-name\Downloads\chromedriver-win64\chromedriver.exe"
```

Make sure the path points to the correct location of your ChromeDriver.

---

## 🚀 How to Run

1. Save the script as `Job.py`.
2. Open a terminal in the project folder.
3. Run the Streamlit app:

   ```sh
   streamlit run Job.py
   ```
4. The app will open in your browser at:

   ```
   http://localhost:8501
   ```

---

## 📂 Usage

1. Select a **job title** from the dropdown.
2. Select a **city** (or choose "All India").
3. Enter the number of jobs to scrape (1–50).
4. Click **Scrape Jobs**.
5. Wait for scraping to finish:

   * Progress bar shows scraping status
   * Preview of jobs appears in a table
6. Download results as:

   * **CSV** file
   * **PDF** file

---

## 📑 Output Example

Each job entry includes:

* Job Title
* Company Name
* Reviews
* Location
* Experience
* Salary
* Posted Date
* Openings
* Applicants
* Job Description
* Role / Industry / Department
* Employment Type
* Education
* Key Skills
* Direct Job URL

---

## 🔮 Future Enhancements

* Add support for non-IT job categories
* Option to schedule automatic scraping
* Email notifications with job results
* Store results in a database

---

## 📜 License

This project is licensed under the **MIT License**.
