from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Data Analysis Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()
        
    def add_image(self, image_path, title):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, title, 0, 1, 'L')
        # Center image
        self.image(image_path, x=15, w=180) 
        self.ln(5)

def generate_chart_images(df, columns):
    """
    Generates static chart images using matplotlib/seaborn.
    Returns a list of dictionaries: [{"title": "...", "path": "..."}]
    """
    images = []
    temp_dir = "temp_charts"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Set style
    sns.set_theme(style="whitegrid")
    
    # 1. Histogram (Numeric)
    numeric_cols = columns.get("numeric", [])
    if numeric_cols:
        col = numeric_cols[0]
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x=col, kde=True, color="skyblue")
        plt.title(f"Distribution of {col}")
        
        filename = f"{temp_dir}/{uuid.uuid4()}_hist.png"
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        images.append({"title": f"Distribution of {col}", "path": filename})
        
    # 2. Bar Chart (Categorical)
    categorical_cols = columns.get("categorical", [])
    if categorical_cols:
        col = categorical_cols[0]
        # Check cardinality to avoid mess
        if df[col].nunique() <= 15:
            data_to_plot = df[col].value_counts().reset_index()
            data_to_plot.columns = [col, "Count"]
            
            plt.figure(figsize=(10, 6))
            sns.barplot(data=data_to_plot, x=col, y="Count", palette="viridis")
            plt.title(f"Count of {col}")
            plt.xticks(rotation=45)
            
            filename = f"{temp_dir}/{uuid.uuid4()}_bar.png"
            plt.savefig(filename, bbox_inches='tight')
            plt.close()
            images.append({"title": f"Count of {col}", "path": filename})
            
    # 3. Scatter Plot (Two Numeric)
    if len(numeric_cols) >= 2:
        col_x = numeric_cols[0]
        col_y = numeric_cols[1]
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x=col_x, y=col_y, color="purple", alpha=0.6)
        plt.title(f"{col_x} vs {col_y}")
        
        filename = f"{temp_dir}/{uuid.uuid4()}_scatter.png"
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        images.append({"title": f"{col_x} vs {col_y}", "path": filename})
        
    # 4. Correlation Heatmap
    if len(numeric_cols) > 2:
        plt.figure(figsize=(10, 8))
        corr = df[numeric_cols].corr()
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Matrix")
        
        filename = f"{temp_dir}/{uuid.uuid4()}_heatmap.png"
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        images.append({"title": "Correlation Matrix", "path": filename})
        
    return images

def generate_pdf_report(analysis_results, df=None, columns=None, filename="report.pdf"):
    pdf = PDFReport()
    pdf.add_page()
    
    # 1. Overview
    pdf.chapter_title("Dataset Overview")
    summary = analysis_results.get("dataset_summary", {}).get("overview", {})
    text = (
        f"Total Records: {summary.get('total_rows', 'N/A')}\n"
        f"Total Columns: {summary.get('total_columns', 'N/A')}\n"
        f"Numeric Columns: {summary.get('numeric_columns', 'N/A')}\n"
        f"Categorical Columns: {summary.get('categorical_columns', 'N/A')}\n"
    )
    pdf.chapter_body(text)
    
    # 2. Key Insights
    pdf.chapter_title("Key Insights")
    insights = analysis_results.get("insights", [])
    if insights:
        text = ""
        for insight in insights:
            text += f"- {insight}\n"
        pdf.chapter_body(text)
    else:
        pdf.chapter_body("No significant insights detected.")

    # 3. Data Cleaning Report
    pdf.chapter_title("Data Cleaning Report")
    cleaning = analysis_results.get("cleaning_report", {}).get("summary", {})
    text = (
        f"Original Rows: {cleaning.get('original_rows', 'N/A')}\n"
        f"Cleaned Rows: {cleaning.get('cleaned_rows', 'N/A')}\n"
        f"Columns Dropped: {cleaning.get('columns_dropped', 0)}\n"
        f"Columns Imputed: {cleaning.get('columns_imputed', 0)}\n"
    )
    pdf.chapter_body(text)
    
    # 4. Visualizations
    if df is not None and columns is not None:
        pdf.add_page()
        pdf.chapter_title("Visualizations")
        
        try:
            images = generate_chart_images(df, columns)
            for img in images:
                if pdf.get_y() > 200: # Check for page break needed
                    pdf.add_page()
                pdf.add_image(img["path"], img["title"])
                
            # Cleanup
            for img in images:
                try:
                    os.remove(img["path"])
                except:
                    pass
        except Exception as e:
            pdf.chapter_body(f"Could not generate charts: {str(e)}")
    
    # 5. Conclusion
    pdf.add_page()
    pdf.chapter_title("Conclusion")
    conclusion = analysis_results.get("conclusion", {})
    text = conclusion.get("summary", "No conclusion generated.")
    pdf.chapter_body(text)
    
    # Output
    return pdf.output(dest='S').encode('latin-1', errors='replace')
