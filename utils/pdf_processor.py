import fitz  # PyMuPDF
from PIL import Image
import io

def pdf_to_images(pdf_path):
    """
    Converts each page of the PDF to a list of PIL Images.
    Uses PyMuPDF to avoid requiring Poppler.
    """
    doc = fitz.open(pdf_path)
    images = []
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
        
    return images

def draw_bounding_boxes(image, fields):
    """
    Draws bounding boxes on the PIL image.
    fields is a list of dicts with 'box_2d' [x1, y1, x2, y2] (1000-normalized).
    """
    from PIL import ImageDraw
    
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    width, height = img_copy.size
    
    for field in fields:
        box = field.get('box_2d')
        if box:
            x1, y1, x2, y2 = box
            # Denormalize (coordinates are 0-1000)
            rect = [
                x1 * width / 1000,
                y1 * height / 1000,
                x2 * width / 1000,
                y2 * height / 1000
            ]
            draw.rectangle(rect, outline="red", width=3)
            
            label = field.get('label')
            if label:
                # Draw label background
                text_pos = (rect[0], rect[1] - 15 if rect[1] > 15 else rect[1])
                draw.text(text_pos, label, fill="red")
                
    return img_copy


def overlay_text(pdf_path, filled_fields, output_path):
    """
    Overlays text onto the PDF based on filled_fields.
    filled_fields is a list of dicts: 
    {
        'page': int (0-indexed),
        'text': str,
        'box_2d': [x1, y1, x2, y2] (1000-normalized)
    }
    """
    doc = fitz.open(pdf_path)
    
    for field in filled_fields:
        page_idx = field.get('page', 0)
        if page_idx >= len(doc):
            continue
            
        page = doc.load_page(page_idx)
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Denormalize coordinates (0-1000)
        x1, y1, x2, y2 = field['box_2d']
        
        rect = fitz.Rect(
            x1 * page_width / 1000,
            y1 * page_height / 1000,
            x2 * page_width / 1000,
            y2 * page_height / 1000
        )
        
        text = field.get('value', '')  # The user input
        print(f"DEBUG: Processing field '{field.get('label')}' with text '{text}'")
        print(f"DEBUG: Box: {field['box_2d']} -> Rect: {rect}")
        
        if text:
            # We insert text. Using a basic fontsize calculation or fixed size.
            # To fit in the box, we might need more complex logic, but fixed size 12 is a start.
            rc = page.insert_textbox(rect, text, fontsize=12, color=(0, 0, 1)) # Blue text to differentiate
            print(f"DEBUG: insert_textbox returned {rc}")
            if rc < 0:
                print("DEBUG: Insertion failed (box might be too small). Trying insert_text at top-left.")
                # Fallback: simple text insertion at top-left of rect
                page.insert_text(rect.tl + (2, 12), text, fontsize=12, color=(0, 0, 1))
            
    doc.save(output_path)
    return output_path
