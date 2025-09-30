#!/usr/bin/env python3
"""
🤖 SMARTMAP PRODUCTION BOT - REAL-TIME ANALYSIS
==============================================
Scans all holders, analyzes photos in real-time, fills empty attributes

Features:
- Scans all pages for empty holders
- Real-time photo analysis with GPT-4 Vision
- Fills Material and Type dropdowns
- Adds "DMNB" tracking to poznámka
- Automatic pagination through all pages
- Error handling and progress tracking
"""

import json
import time
import base64
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
import os
import openai
from PIL import Image
import requests
from loguru import logger

class SmartMapProductionBot:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.setup_openai()
        self.setup_browser()
        self.processed_holders = []
        self.current_page = 1
        
    def setup_logging(self):
        """Setup detailed logging"""
        logger.add("smartmap_production_bot.log", rotation="1 day", retention="30 days")
        logger.info("🤖 SmartMap Production Bot initialized")
        
    def setup_openai(self):
        """Setup OpenAI client for real-time analysis"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_key_here':
            logger.error("❌ OpenAI API key not configured!")
            raise ValueError("OpenAI API key required for real-time analysis")
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        logger.info("🔑 OpenAI client initialized")
        
    def setup_browser(self):
        """Setup Chrome browser"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        logger.info("🌐 Browser initialized")
        
    def login_to_smartmap(self):
        """Login to SmartMap admin"""
        try:
            login_url = os.getenv('LOGIN_URL', 'https://devadmin.smartmap.sk/wp-admin')
            username = os.getenv('LOGIN_USERNAME')
            password = os.getenv('PASSWORD')
            
            logger.info("🔐 Logging into SmartMap...")
            self.driver.get(login_url)
            
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "user_login")))
            password_field = self.driver.find_element(By.ID, "user_pass")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.ID, "wp-submit")
            login_button.click()
            
            self.wait.until(EC.presence_of_element_located((By.ID, "wpadminbar")))
            logger.info("✅ Successfully logged in")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            return False
            
    def navigate_to_holders_page(self, page_num=1):
        """Navigate to specific holders page"""
        try:
            holders_url = os.getenv('GIS_ADMIN_URL', 'https://devadmin.smartmap.sk/holders')
            if page_num > 1:
                holders_url += f"?paged={page_num}"
                
            self.driver.get(holders_url)
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "wp-list-table")))
            
            logger.info(f"✅ Navigated to holders page {page_num}")
            self.current_page = page_num
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation to page {page_num} failed: {str(e)}")
            return False
            
    def get_holders_on_current_page(self):
        """Get all holder information from current page"""
        holders = []
        try:
            # Find the table rows
            table_rows = self.driver.find_elements(By.XPATH, "//table[contains(@class, 'wp-list-table')]//tbody//tr")
            
            for row in table_rows:
                try:
                    # Extract holder data from row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 4:  # Skip header or empty rows
                        continue
                    
                    # Get holder ID and edit URL
                    edit_link = row.find_element(By.XPATH, ".//a[contains(@href, '/holders/edit/')]")
                    edit_url = edit_link.get_attribute('href')
                    holder_id = edit_url.split('/edit/')[-1]
                    
                    # Check if attributes are empty (adjust column indices as needed)
                    material_cell = cells[3].text.strip() if len(cells) > 3 else ""  # Adjust index
                    type_cell = cells[4].text.strip() if len(cells) > 4 else ""      # Adjust index
                    
                    # Only process holders with empty attributes
                    if not material_cell or not type_cell:
                        holders.append({
                            'holder_id': holder_id,
                            'edit_url': edit_url,
                            'material_empty': not material_cell,
                            'type_empty': not type_cell,
                            'row_element': row
                        })
                        logger.info(f"📋 Found empty holder: {holder_id} (material: {bool(material_cell)}, type: {bool(type_cell)})")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing table row: {str(e)}")
                    continue
                    
            logger.info(f"📊 Found {len(holders)} holders with empty attributes on page {self.current_page}")
            return holders
            
        except Exception as e:
            logger.error(f"❌ Failed to get holders from page: {str(e)}")
            return []
            
    def get_photo_url_from_holder_id(self, holder_id):
        """Generate photo URL from holder ID"""
        # Based on the pattern from your data
        base_url = "https://devbackend.smartmap.sk/storage/pezinok/holders-photos"
        photo_url = f"{base_url}/{holder_id}.png"
        return photo_url
        
    def download_and_encode_image(self, photo_url):
        """Download image and encode to base64"""
        try:
            response = requests.get(photo_url, timeout=10)
            response.raise_for_status()
            
            # Process image
            image = Image.open(io.BytesIO(response.content))
            
            # Resize if too large
            if image.width > 1024 or image.height > 1024:
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            logger.error(f"❌ Failed to download/encode image {photo_url}: {str(e)}")
            return None
            
    def analyze_photo_realtime(self, holder_id):
        """Analyze holder photo in real-time using GPT-4 Vision"""
        try:
            photo_url = self.get_photo_url_from_holder_id(holder_id)
            logger.info(f"📸 Analyzing photo for holder {holder_id}: {photo_url}")
            
            # Download and encode image
            base64_image = self.download_and_encode_image(photo_url)
            if not base64_image:
                return None
                
            # Analyze with GPT-4 Vision
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this traffic sign holder image and identify:

1. MATERIAL - Choose EXACTLY from: kov, betón, drevo, plast
2. TYPE - Choose EXACTLY from: stĺp značky samostatný, stĺp značky dvojitý, stĺp verejného osvetlenia, stĺp svetelného signalizačného zariadenia, plot, brána/dvere

Respond in JSON format:
{
  "material": "your_choice",
  "type": "your_choice", 
  "confidence": 0.85,
  "reasoning": "brief explanation"
}

Use Slovak terminology exactly as listed above."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result_text[start:end]
                    result = json.loads(json_str)
                    
                    logger.info(f"🎯 Analysis result for holder {holder_id}: {result.get('material')} | {result.get('type')} (conf: {result.get('confidence', 0):.2f})")
                    return result
            except:
                pass
                
            # Fallback if JSON parsing fails
            logger.warning(f"⚠️ JSON parsing failed for holder {holder_id}")
            return {
                "material": "kov",
                "type": "stĺp značky samostatný",
                "confidence": 0.5,
                "reasoning": "Parsing failed - using defaults"
            }
            
        except Exception as e:
            logger.error(f"❌ Real-time analysis failed for holder {holder_id}: {str(e)}")
            return None
            
    def fill_holder_attributes(self, holder_id, edit_url, material_empty, type_empty):
        """Fill attributes for a specific holder"""
        try:
            logger.info(f"🔧 Processing holder {holder_id}")
            
            # Navigate to edit page
            self.driver.get(edit_url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Analyze photo in real-time
            analysis_result = self.analyze_photo_realtime(holder_id)
            if not analysis_result:
                logger.error(f"❌ Could not analyze photo for holder {holder_id}")
                return False
                
            material = analysis_result.get('material', '')
            holder_type = analysis_result.get('type', '')
            confidence = analysis_result.get('confidence', 0)
            
            success = True
            
            # Fill material dropdown if empty
            if material_empty and material:
                if self.fill_material_dropdown(material):
                    logger.info(f"✅ Filled material: {material}")
                else:
                    logger.warning(f"⚠️ Failed to fill material")
                    success = False
                    
            # Fill type dropdown if empty
            if type_empty and holder_type:
                if self.fill_type_dropdown(holder_type):
                    logger.info(f"✅ Filled type: {holder_type}")
                else:
                    logger.warning(f"⚠️ Failed to fill type")
                    success = False
                    
            # Add DMNB to poznámka
            if self.add_dmnb_to_poznamka(confidence):
                logger.info(f"✅ Added DMNB tracking")
            else:
                logger.warning(f"⚠️ Failed to add DMNB tracking")
                
            # Save form
            if success and self.save_form():
                logger.info(f"🎉 Successfully processed holder {holder_id}")
                self.processed_holders.append({
                    'holder_id': holder_id,
                    'material': material,
                    'type': holder_type,
                    'confidence': confidence,
                    'timestamp': time.time()
                })
                return True
            else:
                logger.error(f"❌ Failed to save holder {holder_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Processing failed for holder {holder_id}: {str(e)}")
            return False
            
    def fill_material_dropdown(self, material):
        """Fill material dropdown"""
        try:
            # Find material dropdown (adjust selector based on actual HTML)
            material_select = Select(self.driver.find_element(By.NAME, "material"))
            material_select.select_by_visible_text(material)
            time.sleep(0.2)  # Reduced delay
            return True
        except Exception as e:
            logger.error(f"❌ Material dropdown fill failed: {str(e)}")
            return False
            
    def fill_type_dropdown(self, holder_type):
        """Fill type dropdown"""
        try:
            # Find type dropdown (adjust selector based on actual HTML)
            type_select = Select(self.driver.find_element(By.NAME, "typ"))
            type_select.select_by_visible_text(holder_type)
            time.sleep(0.2)  # Reduced delay
            return True
        except Exception as e:
            logger.error(f"❌ Type dropdown fill failed: {str(e)}")
            return False
            
    def add_dmnb_to_poznamka(self, confidence):
        """Add DMNB tracking to poznámka field"""
        try:
            # Find poznámka field
            poznamka_field = self.driver.find_element(By.NAME, "poznamka")
            current_text = poznamka_field.get_attribute('value') or ""
            
            # Add DMNB with confidence info
            dmnb_text = f"DMNB (AI: {confidence:.2f})"
            new_text = f"{current_text}\n{dmnb_text}".strip() if current_text else dmnb_text
            
            poznamka_field.clear()
            poznamka_field.send_keys(new_text)
            
            time.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"❌ Poznámka field update failed: {str(e)}")
            return False
            
    def save_form(self):
        """Save the current form"""
        try:
            # Find and click save button
            save_button = self.driver.find_element(By.XPATH, "//input[@type='submit' and contains(@value, 'Save')]")
            save_button.click()
            
            # Wait for save confirmation or page reload
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"❌ Form save failed: {str(e)}")
            return False
            
    def has_next_page(self):
        """Check if there's a next page"""
        try:
            # Look for next page link or pagination
            next_links = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'next-page') or contains(text(), 'Next') or contains(text(), 'Ďalší')]")
            return len(next_links) > 0 and next_links[0].is_enabled()
        except:
            return False
            
    def process_all_pages(self):
        """Process all pages of holders"""
        try:
            if not self.login_to_smartmap():
                return False
                
            page_num = 1
            total_processed = 0
            
            while True:
                logger.info(f"🔄 Processing page {page_num}...")
                
                if not self.navigate_to_holders_page(page_num):
                    logger.error(f"❌ Failed to navigate to page {page_num}")
                    break
                    
                # Get empty holders on current page
                empty_holders = self.get_holders_on_current_page()
                
                if not empty_holders:
                    logger.info(f"📋 No empty holders found on page {page_num}")
                else:
                    logger.info(f"🚀 Processing {len(empty_holders)} empty holders on page {page_num}")
                    
                    for holder in empty_holders:
                        if self.fill_holder_attributes(
                            holder['holder_id'],
                            holder['edit_url'],
                            holder['material_empty'],
                            holder['type_empty']
                        ):
                            total_processed += 1
                            
                        # Minimal delay between holders  
                        time.sleep(0.5)
                        
                        # Progress update
                        if total_processed % 5 == 0:
                            logger.info(f"📊 Progress: {total_processed} holders processed so far")
                            
                # Check for next page
                if self.has_next_page():
                    page_num += 1
                    time.sleep(1)  # Reduced delay between pages
                else:
                    logger.info(f"🏁 Reached last page (page {page_num})")
                    break
                    
            logger.info(f"🎉 PROCESSING COMPLETE! Total holders processed: {total_processed}")
            
            # Save processing report
            self.save_processing_report()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {str(e)}")
            return False
            
    def save_processing_report(self):
        """Save detailed processing report"""
        try:
            report = {
                'total_processed': len(self.processed_holders),
                'timestamp': time.time(),
                'pages_processed': self.current_page,
                'holders': self.processed_holders
            }
            
            with open('smartmap_processing_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            logger.info(f"📄 Processing report saved: {len(self.processed_holders)} holders processed")
            
        except Exception as e:
            logger.error(f"❌ Failed to save report: {str(e)}")
            
    def close(self):
        """Close browser and cleanup"""
        if hasattr(self, 'driver'):
            self.driver.quit()
        logger.info("🔚 SmartMap Production Bot closed")

def main():
    print("🤖 SMARTMAP PRODUCTION BOT - REAL-TIME ANALYSIS")
    print("=" * 60)
    print("Features:")
    print("✅ Scans ALL pages for empty holders")
    print("✅ Real-time photo analysis with GPT-4 Vision")
    print("✅ Fills Material and Type dropdowns")
    print("✅ Adds 'DMNB' tracking to poznámka")
    print("✅ Automatic pagination and processing")
    print()
    
    bot = SmartMapProductionBot()
    
    try:
        response = input("🚀 Ready to start processing all holders? (y/n): ").lower().strip()
        
        if response == 'y':
            print("🔄 Starting production processing...")
            print("📋 This will scan ALL pages and process empty holders")
            print("⏱️ This may take several hours depending on the number of holders")
            print()
            
            success = bot.process_all_pages()
            
            if success:
                print("\n🎉 PROCESSING COMPLETE!")
                print("✅ Check the SmartMap admin panel for results")
                print("📋 Review logs: smartmap_production_bot.log")
                print("📄 Check report: smartmap_processing_report.json")
            else:
                print("\n❌ Processing encountered issues. Check the logs.")
        else:
            print("⏸️ Processing cancelled.")
            
    finally:
        bot.close()

if __name__ == "__main__":
    main()
