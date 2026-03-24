
import zipfile
import re
import xml.etree.ElementTree as ET
import sys

def get_merge_fields(docx_path):
    document_xml_path = 'word/document.xml'
    
    try:
        with zipfile.ZipFile(docx_path) as z:
            with z.open(document_xml_path) as f:
                xml_content = f.read()
    except KeyError:
        print(f"Error: Could not find {document_xml_path} in the docx file.")
        return
    except Exception as e:
        print(f"Error opening docx file: {e}")
        return

    # XML namespaces
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    root = ET.fromstring(xml_content)
    
    fields = []
    
    # Method 1: finding w:instrText directly (often split across runs)
    # We will look for text containing MERGEFIELD
    
    # Helper to reconstruct instructions from runs
    current_instr = ""
    extracting = False
    
    # Iterate over all text elements in the document
    # This is a simplified parser; field codes can be complex
    for text_node in root.findall('.//w:t', ns):
        text = text_node.text or ""
        
        # Check for simple field start/end or just text aggregation
        # In many cases, the instruction is inside <w:instrText> not <w:t>
        pass

    # Better approach: Look for w:instrText elements
    for instr_node in root.findall('.//w:instrText', ns):
        text = instr_node.text or ""
        if 'MERGEFIELD' in text:
            # Clean up the field definition
            # Format is usually: MERGEFIELD  FieldName  \* MERGEFORMAT
            match = re.search(r'MERGEFIELD\s+"?([^"\s\\]+)"?', text)
            if match:
                 fields.append(match.group(1))
            else:
                # Try laxer match
                 parts = text.strip().split()
                 if len(parts) > 1 and parts[0] == 'MERGEFIELD':
                     fields.append(parts[1].replace('"', ''))
    
    # Method 2: Check for simple fields <w:fldSimple>
    for fldSimple in root.findall('.//w:fldSimple', ns):
        instr = fldSimple.get(f'{ns["w"]}instr')
        if instr and 'MERGEFIELD' in instr:
             match = re.search(r'MERGEFIELD\s+"?([^"\s\\]+)"?', instr)
             if match:
                 fields.append(match.group(1))

    return sorted(list(set(fields)))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_docx.py <docx_file>")
        sys.exit(1)
        
    docx_file = sys.argv[1]
    fields = get_merge_fields(docx_file)
    print("Found Merge Fields:")
    for f in fields:
        print(f"- {f}")
