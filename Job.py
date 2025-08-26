import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import csv
import re
import os
from urllib.parse import quote
from fpdf import FPDF


# Streamlit UI
st.title("Naukri Job Scraper")
st.write("This app scrapes job listings from Naukri.com based on your criteria.")


# Predefined options for dropdowns
it_job_titles = [
    "Data Scientist",
    "Software Engineer",
    "Web Developer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Data Engineer",
    "Machine Learning Engineer",
    "AI Engineer",
    "Big Data Engineer",
    "Database Administrator",
    "Systems Administrator",
    "Network Engineer",
    "Cyber Security Analyst",
    "IT Support Engineer",
    "Mobile App Developer",
    "UI/UX Designer",
    "Product Manager",
    "Project Manager",
    "Business Analyst",
    "QA Engineer",
    "Embedded Systems Engineer",
    "Blockchain Developer",
]

indian_cities = [
    "All India",
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Gurgaon",
    "Noida",
    "Jaipur",
    "Lucknow",
    "Chandigarh",
    "Indore",
    "Bhopal",
    "Coimbatore",
    "Vadodara",
    "Nagpur",
    "Visakhapatnam",
    "Kochi",
    "Patna",
    "Bhubaneswar",
    "Surat",
]


# User inputs with dropdowns
job_title = st.selectbox("Select job title", it_job_titles, index=0)
city = st.selectbox("Select city", indian_cities, index=0)
num_jobs = st.number_input(
    "Number of jobs to scrape", min_value=1, max_value=50, value=5
)
run_button = st.button("Scrape Jobs")


# Initialize session state for job data
if "job_data_list" not in st.session_state:
    st.session_state.job_data_list = []
if "global_job_id" not in st.session_state:
    st.session_state.global_job_id = 1


# Utility to clean multiline text preserving line breaks and bullets
def clean_multiline_text(text):
    if not text or text == "NA":
        return "NA"
    # Replace HTML <br> tags with newlines if any
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    # Normalize multiple newlines to two newlines for paragraph breaks
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    # Convert bullet-like characters or dashes preceded by spaces to newline + bullet
    text = re.sub(r"(\s*[-–•]\s*)", r"\n- ", text)
    # Strip spaces on each line
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def get_text(driver, xpath):
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text.strip()
    except:
        return "NA"


def get_html(driver, xpath):
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.get_attribute("innerHTML")
    except:
        return "NA"


def extract_company_and_reviews(company_text):
    reviews = "NA"
    match = re.search(
        r"(\d+\.\d+)\s*Reviews", company_text
    )  # Extract reviews if present
    if match:
        reviews = match.group(1)
        company_text = company_text.replace(match.group(0), "").strip()
    return company_text, reviews


def clean_key_skills(key_skills_html):
    try:
        soup = BeautifulSoup(key_skills_html, "html.parser")
        spans = soup.find_all("span")
        skills_list = [span.get_text(strip=True) for span in spans]
        return ", ".join(skills_list)
    except:
        return "NA"


def clean_education(education_text):
    return education_text.replace("Education", "").strip()


def extract_job_details(driver, job_element):
    try:
        raw_url = job_element.find_element(By.TAG_NAME, "a").get_attribute("href")
        job_url = raw_url.split("?")[0] if "?" in raw_url else raw_url  # Clean URL

        driver.execute_script(
            "window.open(arguments[0], '_blank');", job_url
        )  # Open in new tab
        driver.switch_to.window(driver.window_handles[-1])  # Switch to new tab

        # Wait for job details to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "styles_job-header-container___0wLZ")
                )
            )
        except:
            st.warning("Job details page didn't load properly")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return None

        # Click 'read more' if present to expand full description
        try:
            read_more = driver.find_element(
                By.XPATH,
                "//span[contains(text(),'read more') or contains(text(),'Read more') or contains(text(),'Read More') or contains(text(),'see more')]",
            )
            driver.execute_script("arguments[0].click();", read_more)
            time.sleep(1)
        except Exception:
            pass

        job_title_text = get_text(
            driver, "//h1[contains(@class, 'styles_jd-header-title__rZwM1')]"
        )
        company_text_raw = get_text(
            driver, "//div[contains(@class, 'styles_jd-header-comp-name__MvqAI')]"
        )
        company_text, reviews_text = extract_company_and_reviews(company_text_raw)
        location_text = get_text(
            driver, "//div[contains(@class, 'styles_jhc__loc___Du2H')]"
        )

        # Filter for city
        if city != "All India" and city.lower() not in location_text.lower():
            st.warning(f"Skipping non-{city} job: {location_text}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])  # Switch back to main tab
            return None

        experience_text = get_text(
            driver, "//div[contains(@class, 'styles_jhc__exp__k_giM')]"
        )
        salary_text = get_text(
            driver, "//div[contains(@class, 'styles_jhc__salary__jdfEC')]"
        )

        job_details_parent_xpath = (
            "//div[contains(@class, 'styles_jhc__jd-stats__KrId0')]"
        )
        posted_on_text = get_text(
            driver,
            f"{job_details_parent_xpath}//span[normalize-space(label)='Posted:']/span",
        )
        openings_text = get_text(
            driver,
            f"{job_details_parent_xpath}//span[normalize-space(label)='Openings:']/span",  #
        )
        applications_text = get_text(
            driver,
            f"{job_details_parent_xpath}//span[normalize-space(label)='Applicants:']/span",  # Changed 'Applications' to 'Applicants' as per actual site text
        )

        other_details_parent_xpath = (
            "//div[contains(@class, 'styles_other-details__oEN4O')]"
        )
        role_text = get_text(
            driver, f"{other_details_parent_xpath}//div[contains(label, 'Role:')]/span"
        )  # Changed 'Job Role' to 'Role' as per actual site text
        industry_type_text = get_text(
            driver,
            f"{other_details_parent_xpath}//div[contains(label, 'Industry Type:')]/span",
        )
        department_text = get_text(
            driver,
            f"{other_details_parent_xpath}//div[contains(label, 'Department:')]/span",
        )
        employment_type_text = get_text(
            driver,
            f"{other_details_parent_xpath}//div[contains(label, 'Employment Type:')]/span",
        )
        role_category_text = get_text(
            driver,
            f"{other_details_parent_xpath}//div[contains(label, 'Role Category:')]/span",
        )

        education_text_raw = get_text(
            driver, "//div[contains(@class, 'styles_education__KXFkO')]"
        )
        education_text = clean_education(education_text_raw)

        key_skills_html = get_html(
            driver, "//div[contains(@class, 'styles_key-skill__GIPn_')]"
        )
        key_skills_text = clean_key_skills(key_skills_html)

        job_desc_raw = get_text(
            driver, "//div[contains(@class, 'styles_JDC__dang-inner-html__h0K4t')]"
        )
        job_desc_text = clean_multiline_text(job_desc_raw)

        job_data = {
            "Job ID": st.session_state.global_job_id,
            "Job Title": job_title_text if job_title_text else "NA",
            "Company": company_text if company_text else "NA",
            "Reviews": reviews_text if reviews_text else "NA",
            "Location": location_text if location_text else "NA",
            "Experience": experience_text if experience_text else "NA",
            "Salary": salary_text if salary_text else "NA",
            "Posted On": posted_on_text if posted_on_text else "NA",
            "Openings": openings_text if openings_text else "NA",
            "Applications": applications_text if applications_text else "NA",
            "Job Description": job_desc_text if job_desc_text else "NA",
            "Role": role_text if role_text else "NA",
            "Industry Type": industry_type_text if industry_type_text else "NA",
            "Department": department_text if department_text else "NA",
            "Employment Type": employment_type_text if employment_type_text else "NA",
            "Role Category": role_category_text if role_category_text else "NA",
            "Education": education_text if education_text else "NA",
            "Key Skills": key_skills_text if key_skills_text else "NA",
            "Job URL": f'=HYPERLINK("{job_url}", "View Job")' if job_url else "NA",
        }

        st.session_state.global_job_id += 1
        driver.close()
        driver.switch_to.window(driver.window_handles[0])  # Switch back to main tab
        return job_data

    except Exception as e:
        st.error(f"Error processing job {st.session_state.global_job_id}: {e}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        return None


def scrape_jobs_from_category(driver, url, job_count):
    page_number = 1
    total_jobs_collected = 0
    progress_bar = st.progress(0)
    status_text = st.empty()

    while total_jobs_collected < job_count:
        status_text.text(
            f"Scraping page {page_number}... ({total_jobs_collected}/{job_count} jobs collected)"
        )
        progress_bar.progress(total_jobs_collected / job_count)

        current_url = f"{url}-{page_number}" if page_number > 1 else url
        driver.get(current_url)

        try:
            WebDriverWait(driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located(
                        (
                            By.CLASS_NAME,
                            "srp-jobtuple-wrapper",
                        )  # Waits for an element with class name "srp-jobtuple-wrapper" to appear in the DOM
                    ),
                    EC.presence_of_element_located((By.CLASS_NAME, "jobTuple")),
                )
            )
        except:
            st.warning(f"Page load failed or no jobs found at {current_url}")
            break

        job_list = driver.find_elements(By.CLASS_NAME, "srp-jobtuple-wrapper")
        if not job_list:
            job_list = driver.find_elements(By.CLASS_NAME, "jobTuple")

        if not job_list:
            st.warning("No job listings found on the page.")
            break

        for i in range(len(job_list)):
            if total_jobs_collected >= job_count:
                break
            try:
                job_data = extract_job_details(driver, job_list[i])
                if job_data:
                    st.session_state.job_data_list.append(job_data)
                    total_jobs_collected += 1
                    time.sleep(2)
            except Exception as e:
                st.error(
                    f"Error processing job element {total_jobs_collected + 1}: {e}"
                )

        if total_jobs_collected < job_count:
            page_number += 1
            time.sleep(3)

    progress_bar.progress(1.0)
    status_text.text(f"Completed! Collected {total_jobs_collected} jobs.")
    return total_jobs_collected


def save_to_csv(data, filename):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Job ID",
            "Job Title",
            "Company",
            "Reviews",
            "Location",
            "Experience",
            "Salary",
            "Posted On",
            "Openings",
            "Applications",
            "Job Description",
            "Role",
            "Industry Type",
            "Department",
            "Employment Type",
            "Role Category",
            "Education",
            "Key Skills",
            "Job URL",
        ]
        writer = csv.DictWriter(
            csvfile, fieldnames=fieldnames
        )  # Use DictWriter for better handling of dictionaries
        writer.writeheader()  # Write header row
        for job_data in data:
            writer.writerow(job_data)  # Write each job data as a row


def save_to_pdf(data, filename, city_name, job_title_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Naukri.com Job Listings", ln=True, align="C")

    # Add Job Title and City info below the title
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Job Title: {job_title_name}", ln=True, align="C")
    pdf.cell(0, 10, f"City: {city_name}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 10)
    line_height = 6
    label_width = 40
    page_width = pdf.w - 2 * pdf.l_margin
    value_width = page_width - label_width

    for job in data:
        for key, value in job.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                value = "NA"
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", "B")
            pdf.cell(label_width, line_height, f"{key}:", border=0)

            pdf.set_font("Arial", "")
            if key == "Job URL":
                match = re.search(r'HYPERLINK\("([^"]+)"', value)
                url_link = match.group(1) if match else ""
                pdf.set_text_color(0, 0, 255)
                pdf.ln(line_height)
                y_before = pdf.get_y()
                pdf.set_xy(pdf.l_margin + label_width, y_before)
                pdf.set_font("Arial", "U")
                pdf.cell(value_width, line_height, url_link, link=url_link)
                pdf.set_font("Arial", "")
                pdf.set_text_color(0, 0, 0)
                pdf.ln(line_height)
            else:
                pdf.multi_cell(value_width, line_height, str(value))

        pdf.ln(1)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(5)

    pdf.output(filename)


def run_scraper():
    chrome_driver_path = r"C:\Users\your-system-name\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
    service = Service(chrome_driver_path)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    driver = webdriver.Chrome(service=service, options=options)

    try:
        job_search = quote(job_title.lower().replace(" ", "-"))

        if city == "All India":
            base_url = f"https://www.naukri.com/{job_search}-jobs"
        else:
            city_search = quote(city.lower())
            base_url = f"https://www.naukri.com/{job_search}-jobs-in-{city_search}"

        st.info(f"Scraping URL: {base_url}")

        st.session_state.job_data_list = []
        st.session_state.global_job_id = 1

        jobs_collected = scrape_jobs_from_category(driver, base_url, num_jobs)

        if jobs_collected > 0:
            csv_filename = f"naukri_{job_title.lower().replace(' ', '_')}_{city.lower().replace(' ', '_')}_jobs.csv"
            save_to_csv(st.session_state.job_data_list, csv_filename)

            pdf_filename = f"naukri_{job_title.lower().replace(' ', '_')}_{city.lower().replace(' ', '_')}_jobs.pdf"
            save_to_pdf(st.session_state.job_data_list, pdf_filename, city, job_title)

            st.success(f"Successfully scraped {jobs_collected} jobs!")

            st.subheader("Scraped Job Data Preview")
            st.dataframe(st.session_state.job_data_list)

            col1, col2 = st.columns(2)
            with col1:
                with open(csv_filename, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=csv_filename,
                        mime="text/csv",
                    )
            with col2:
                with open(pdf_filename, "rb") as file:
                    st.download_button(
                        label="Download PDF",
                        data=file,
                        file_name=pdf_filename,
                        mime="application/pdf",
                    )

            os.remove(csv_filename)
            os.remove(pdf_filename)
        else:
            st.warning("No jobs were scraped. Please try different search criteria.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        driver.quit()


if run_button:
    run_scraper()
