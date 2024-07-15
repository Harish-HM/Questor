from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import ExcelUploadForm,CleanOptionsForm,LinkOptionsForm,KeywordUploadForm,URLInputForm
import pandas as pd
import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from openpyxl import Workbook
from tkinter import filedialog, messagebox
from openpyxl import Workbook
import pandas as pd
import re
import io
# def home(request):
#     return render(request, 'extractor/home.html')


class EmailExtractorTool:
    keywords = [
        "contact", "about", "our team", "advertising", "write for us",
        "media kit", "media", "press", "get in touch", "editorial",
        "support", "FAQ", "privacy policy", "about us", "advertise with us",
        "advertise", "contact us", "contact me", "write to us", "guest post"
    ]

    @staticmethod
    def send_error_email(error_message):
        sender_email = "your_email@example.com"
        receiver_email = "your_email@example.com"
        password = "your_email_password"  # Use app-specific password

        message = MIMEMultipart()
        message["Subject"] = "Error Notification from Email Extractor Tool"
        message["From"] = sender_email
        message["To"] = receiver_email

        body = f"An error occurred:\n\n{error_message}"
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            print("Error email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {str(e)}")

    @staticmethod
    def extract_emails(url):
        emails = []
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            emails += re.findall(r'\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.(?:com|ht|co|it|ai|io|fr|org|net|info|biz|name|pro|aero|coop|museum|asia|cat|jobs|mobi|tel|travel|xxx|post|edu|gov|mil|int|in))\b', response.text)

            links = [a['href'] for a in soup.find_all('a', href=True) if any(keyword in a['href'] for keyword in EmailExtractorTool.keywords)]

            for link in links:
                if not link.startswith("http"):
                    link = requests.compat.urljoin(url, link)
                try:
                    response = requests.get(link)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    emails += re.findall(r'\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.(?:com|ht|co|it|ai|io|fr|org|net|info|biz|name|pro|aero|coop|museum|asia|cat|jobs|mobi|tel|travel|xxx|post|edu|gov|mil|int|in))\b', response.text)
                except requests.exceptions.RequestException as e:
                    EmailExtractorTool.send_error_email(f"Error extracting emails from {link}: {str(e)}")
                    continue

            if not emails:
                emails.append("Email not found")

        except requests.exceptions.RequestException as e:
            error_message = f"Error extracting emails from {url}: {str(e)}"
            print(error_message)
            EmailExtractorTool.send_error_email(error_message)
            emails.append("Email extraction error")

        return list(set(emails))

def handle_uploaded_file(excel_file):
    return pd.read_excel(excel_file)

def extract_emails_view(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            # Read the uploaded Excel file directly from the uploaded file object
            df = handle_uploaded_file(excel_file)
            data = []
            for index, row in df.iterrows():
                url = row['URL']  # Ensure the column name in the Excel file is 'URL'
                emails = EmailExtractorTool.extract_emails(url)
                for email in emails:
                    data.append({'URL': url, 'Email': email})
            result_df = pd.DataFrame(data)
            
            # Prepare the response as a downloadable Excel file
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=extracted_emails.xlsx'
            result_df.to_excel(response, index=False)
            return response
    else:
        form = ExcelUploadForm()
    return render(request, 'extractor/extract_emails.html', {'form': form})

api_key = "2cba55ea8599d0e8a86086ddd18c6a98f9fb548ce68be95b1a941358d903e18f"  # Replace with your actual SerpApi key

def send_error_email(error_message):
    sender_email = "your_email@example.com"
    receiver_email = "your_email@example.com"
    password = "your_email_password"
    
    message = MIMEMultipart()
    message["Subject"] = "Error Notification from Google Search Results App"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    body = f"An error occurred:\n\n{error_message}"
    message.attach(MIMEText(body, "plain"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Error email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def validate_url(url):
    if not urlparse(url).scheme:
        return "http://" + url
    return url

def parse_index_filter(index_filter_str):
    index_filter = set()
    ranges = index_filter_str.split(',')
    for r in ranges:
        if '-' in r:
            start, end = map(int, r.split('-'))
            index_filter.update(range(start, end + 1))
        else:
            index_filter.add(int(r))
    return sorted(index_filter)

def get_search_results(location, keywords, index_filter):
    results = []
    num_results_per_page = 200
    total_pages = 20

    for keyword in keywords:
        for page in range(total_pages):
            params = {
                "q": keyword,
                "location": location,
                "hl": "en",
                "gl": "us",
                "device": "desktop",
                "api_key": api_key,
                "start": page * num_results_per_page,
                "num": num_results_per_page
            }

            try:
                response = requests.get("https://serpapi.com/search", params=params)
                response.raise_for_status()
                data = response.json()

                for position, result in enumerate(data.get("organic_results", []), start=1 + page * num_results_per_page):
                    if position in index_filter:
                        main_domain = get_main_domain(result.get("link", ""))
                        link_count = count_links_on_homepage(main_domain)
                        has_advertising_page = check_for_advertising_page(main_domain)
                        results.append({
                            "Keyword": keyword,
                            "Position": position,
                            "Title": result.get("title", ""),
                            "Link": result.get("link", ""),
                            "Snippet": result.get("snippet", ""),
                            "Main Domain": main_domain,
                            "Link Count": link_count,
                            "Has Advertising Page": has_advertising_page
                        })

                if len(data.get("organic_results", [])) < num_results_per_page:
                    break
            except Exception as e:
                error_message = f"Error fetching search results for keyword '{keyword}' on page {page + 1}: {str(e)}"
                send_error_email(error_message)
                break
    return results

def get_main_domain(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

def count_links_on_homepage(main_domain):
    try:
        response = requests.get(main_domain, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a")
        return len(links)
    except Exception:
        return "ERROR"

def check_for_advertising_page(main_domain):
    advertising_keywords = ["advertising", "advertise", "advertise with us"]
    try:
        response = requests.get(main_domain, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        page_text = soup.get_text().lower()
        for keyword in advertising_keywords:
            if keyword in page_text:
                return True
        return False
    except Exception:
        return False

def write_links_to_excel(results, response):
    df = pd.DataFrame(results)
    
    if 'Link' in df.columns and 'Main Domain' in df.columns:
        df_links = df[['Main Domain', 'Link']].rename(columns={'Link': 'LINKS'})
    else:
        raise ValueError("Columns 'Link' and/or 'Main Domain' not found in the results DataFrame.")
    
    # Ensure 'Link Count' is an integer
    df['Link Count'] = pd.to_numeric(df['Link Count'], errors='coerce')

    with pd.ExcelWriter(response) as writer:
        df_links.to_excel(writer, sheet_name="All Links", index=False)
        
        if 'Main Domain' in df.columns:
            df_www = df[df['Main Domain'].str.contains("www.")]
            df_non_www = df[~df['Main Domain'].str.contains("www.")]
            df_links_50_plus = df[df['Link Count'] >= 50]
            df_advertising_pages = df[df['Has Advertising Page'] == True]
            
            df_www.to_excel(writer, sheet_name="With www", index=False)
            df_non_www.to_excel(writer, sheet_name="Without www", index=False)
            df_links_50_plus.to_excel(writer, sheet_name="50+ Link Counts", index=False)
            df_advertising_pages.to_excel(writer, sheet_name="Advertising Pages", index=False)

def fetch_links_view(request):
    if request.method == 'POST':
        upload_form = ExcelUploadForm(request.POST, request.FILES)
        options_form = LinkOptionsForm(request.POST)
        
        if upload_form.is_valid() and options_form.is_valid():
            excel_file = request.FILES['excel_file']
            
            # Read uploaded Excel file into pandas DataFrame
            df = pd.read_excel(excel_file)
            keywords = df['Keyword']  # Ensure the column name in the Excel file is 'Keyword'
            index_filter_str = options_form.cleaned_data['index_filter']
            index_filter = parse_index_filter(index_filter_str)

            # Fetch links for each keyword
            search_results = get_search_results("India", keywords, index_filter)

            result_df = pd.DataFrame(search_results)
            
            # Prepare the response as a downloadable Excel file
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=fetched_links.xlsx'
            write_links_to_excel(result_df, response)
            return response
    else:
        upload_form = ExcelUploadForm()
        options_form = LinkOptionsForm()
    
    return render(request, 'extractor/fetch_links.html', {'upload_form': upload_form, 'options_form': options_form})

# this is keyword extractor code
def extract_segment(url):
    pattern = r'[^/]+(?=/[^/]*$)'
    match = re.search(pattern, url)
    if match:
        segment = match.group(0).replace('-', ' ')
        return segment
    else:
        return 'Keyword not found'

def extract_keywords_view(request):
    keyword_result = None
    form = ExcelUploadForm()
    single_url_form = URLInputForm()
    
    if request.method == 'POST':
        if 'excel_file' in request.FILES:
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']
                df = pd.read_excel(excel_file)
                result = {}

                for index, row in df.iterrows():
                    url = row['URL']
                    segment = extract_segment(url)
                    result[url] = segment

                # Create an in-memory output file
                output = io.BytesIO()
                workbook = Workbook()
                worksheet = workbook.active
                worksheet.append(["URLs", "Extracted Keyword"])

                for url, segment in result.items():
                    worksheet.append([url, segment])

                workbook.save(output)
                output.seek(0)

                response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=extracted_keywords.xlsx'
                return response
        elif 'single_url' in request.POST:
            single_url_form = URLInputForm(request.POST)
            if single_url_form.is_valid():
                single_url = single_url_form.cleaned_data['single_url']
                keyword_result = extract_segment(single_url)
    
    return render(request, 'extractor/extract_keywords.html', {
        'form': form,
        'single_url_form': single_url_form,
        'keyword_result': keyword_result
    })