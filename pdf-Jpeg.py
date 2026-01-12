from pdf2image import convert_from_path
import os

os.makedirs('Constitution-of-Nepal', exist_ok=True)

# Update with your actual path
poppler_path = r'C:\Program Files\poppler-25.07.0\Library\bin'  # or \bin if no Library folder

print("Starting PDF conversion...")
print("This may take a few minutes for large PDFs...")

try:
    pages = convert_from_path(
        'Constitution of Nepal.pdf',
        dpi=300,
        poppler_path=poppler_path
    )
    
    print(f"Successfully loaded {len(pages)} pages")
    
    for i, page in enumerate(pages):
        print(f"Converting page {i+1}/{len(pages)} to JPEG...")
        page.save(f'Constitution-of-Nepal/Page_{i+1}.jpg', 'JPEG')
    
    print("Conversion complete!")
    
except FileNotFoundError:
    print("Error: Could not find 'Constitution of Nepal.pdf'")
    print("Make sure the PDF file is in the same folder as this script")
    
except Exception as e:
    print(f"Error occurred: {e}")