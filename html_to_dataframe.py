import sys
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
import re

####################################################################################################
# BRIEFING /----------------------------------------------------------------------------------------
# This application was created mainly for use with Hotmart search pages, but without the need for scraping, so as not to infringe any rules.
# The data is manually collected from the website, by Copy & Pasting the HTML code and saving it as a TXT file, then the application searches the TXT file and converts all relevant data into a DataFrame and exports it as a CSV file.
####################################################################################################

# Open the TXT file and get its text
def get_file_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "\nERROR: File Not Found!\n"
    except Exception as e:
        return f"\nERROR:\n{e}\n"


#
def extract_info_from_divs(html, class_name):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        divs = soup.find_all('div', class_=class_name)
        result = []
        
        for div in divs:
            info = {}

            # Extract image src from <img> inside the <div>
            img = div.find('img')
            if img and 'src' in img.attrs:
                info['img_src'] = img['src']

            # Extract text from <span> with class "product-name" inside the <div>
            span = div.find('span', class_='product-name')
            if span:
                info['product_name'] = span.get_text()

            # Extract text from <p> with specified class inside the <div>
            p = div.find('p', class_='_mb-0 _text-3 _text-md-4 _text-green _font-weight-light')
            if p:
                p_text = p.get_text().strip()
                parts = p_text.split(maxsplit=1)  # Split into at most 2 parts
                if len(parts) == 2:
                    info['currency'] = parts[0]  # The currency part
                    info['commission'] = float(parts[1].replace('.', '').replace(',', '.'))  # The numeric part
                else:
                    info['commission'] = float(p_text.replace('.', '').replace(',', '.'))  # Fallback
            else:
                info['currency'] = " "
                info['commission'] = 0.0

            # Extract text from another <p> with class "_mb-0 _text-1 _text-gray-500"
            max_price_p = div.find('p', class_='_mb-0 _text-1 _text-gray-500')
            if max_price_p:
                max_price_text = max_price_p.get_text().strip()
                match = re.search(r'[\d.,]+', max_price_text)
                if match:
                    numeric_value = match.group(0).replace('.', '').replace(',', '.')
                    info['max_price'] = float(numeric_value)
                else:
                    info['max_price'] = 0.0  # Default value if not found
            else:
                info['max_price'] = 0.0  # Default value if not found

            # Extract all <span> elements with class "_mr-1 _text-1 _text-gray-800"
            comment_rating_spans = div.find_all('span', class_='_mr-1 _text-1 _text-gray-800')
            if comment_rating_spans:
                # Get the first <span> for comment_rating
                info['comment_rating'] = float(comment_rating_spans[0].get_text().strip())
                # Get the second <span> for temperature
                if len(comment_rating_spans) > 1:
                    temperature_text = comment_rating_spans[1].get_text().strip()
                    info['temperature'] = int(temperature_text.replace('°', ''))  # Remove '°' and convert to int
                else:
                    info['temperature'] = 0  # Default value if second span not found
            else:
                info['comment_rating'] = 0.0  # Default value if not found
                info['temperature'] = 0  # Default value if not found

            # Extract text from <span> with class "_ml-1 _text-1 _text-gray-500 _font-weight _d-none _d-md-inline" for comments
            comments_span = div.find('span', class_='_ml-1 _text-1 _text-gray-500 _font-weight _d-none _d-md-inline')
            if comments_span:
                comments_text = comments_span.get_text().strip()
                numeric_comments = comments_text.replace('(', '').replace(')', '').replace('.', '')
                info['comments'] = int(numeric_comments)  # Convert to int
            else:
                info['comments'] = 0  # Default value if not found

            # Only add to result if we found something useful
            if info:
                result.append(info)
        
        return result

    except Exception as e:
        return f"An error occurred: {e}"


#

def create_dataframe(info_list, csv_file_name=None):
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(info_list)
    
    # If a filename is provided, export the DataFrame to a CSV file
    if csv_file_name:
        df.to_csv(f'{csv_file_name}.csv', index=False, encoding='utf-8-sig')
    
    # Reorder columns
    df = df[['product_name', 'currency', 'commission', 'max_price',
       'comment_rating', 'comments', 'temperature', 'img_src']]
    return df



#

def create_interactive_scatter_plot(df, file_name='scatter_plot.html'):
    # df filter
    df = df[df["comment_rating"]>0]
    
    # Create a scatter plot with Plotly
    fig = px.scatter(
        df,
        x='max_price',
        y='commission',
        size='comment_rating',
        color='temperature',
        color_continuous_scale='OrRd',
        range_color=[0, 150],
        title='Scatter Plot of Commission vs Max Price with Regression Line<br><span>Filtered by comment_rating > 0</span>',
        hover_name='product_name',
        hover_data=['currency', 'commission', 'max_price', 'comment_rating', 'comments', 'temperature'],
        trendline='ols'  # Adds the regression line
    )
    
    # Update layout for dark theme
    fig.update_layout(template='plotly_dark')
    
    # Save the plot to an HTML file
    fig.write_html(file_name)



####################################################################################################
# INPUT ############################################################################################
####################################################################################################

file_path = "test_html.txt"
html = get_file_text(file_path)
print(f'\n{html[-10:]}\n')

# product_name_list = extract_span_by_class(html, "product-name")
# print(f'\n{product_name_list}\n')

# cover_url_list = extract_img_src_by_class(html, "_h-full")
# print(f'\n{cover_url_list}\n')

info_list = extract_info_from_divs(html, "hot-col-xl-3 hot-col-lg-4 hot-col-md-6 hot-col-sm-12 _py-3")
print(f'\n{info_list}\n')
print(f'\n{info_list[0]}\n')
print(f'\n{info_list[8]}\n')
print(f'\n{info_list[9]}\n')

df = create_dataframe(info_list, "test_")
print(f'\n{df}\n')
create_interactive_scatter_plot(df, file_name='scatter_plot.html')
