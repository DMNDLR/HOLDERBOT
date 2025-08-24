"""
Web Automation Module for GIS Traffic Sign Bot
Handles browser automation, login, and navigation
"""

import time
import os
from typing import Optional, Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

from config.config import Config


class GISWebAutomation:
    """Main class for GIS website automation"""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.is_logged_in = False
        
        # Setup logging
        logger.add(Config.LOG_FILE, rotation="10 MB", level=Config.LOG_LEVEL)
        logger.info("GIS Web Automation Bot initialized")
    
    def setup_browser(self) -> bool:
        """Initialize and configure the browser"""
        try:
            logger.info("Setting up browser...")
            
            # Setup Chrome options
            chrome_options = Options()
            
            if Config.HEADLESS_MODE:
                chrome_options.add_argument("--headless")
                logger.info("Running in headless mode")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Setup webdriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configure implicit wait and maximize window
            self.driver.implicitly_wait(Config.IMPLICIT_WAIT)
            self.driver.maximize_window()
            
            # Setup explicit wait
            self.wait = WebDriverWait(self.driver, Config.WAIT_TIMEOUT)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            return False
    
    def login_to_wordpress(self) -> bool:
        """Login to WordPress admin panel"""
        try:
            logger.info("Attempting to login to WordPress...")
            
            if not self.driver:
                logger.error("Browser not initialized")
                return False
            
            # Navigate to login page
            self.driver.get(Config.LOGIN_URL)
            logger.info(f"Navigating to login page: {Config.LOGIN_URL}")
            
            # Wait for login form to load
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "user_login"))
            )
            
            password_field = self.driver.find_element(By.ID, "user_pass")
            login_button = self.driver.find_element(By.ID, "wp-submit")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(Config.USERNAME)
            
            password_field.clear()
            password_field.send_keys(Config.PASSWORD)
            
            logger.info("Credentials entered, submitting login form...")
            
            # Submit login form
            login_button.click()
            
            # Wait for login to complete
            time.sleep(3)
            
            # Check if login was successful
            if "wp-admin" in self.driver.current_url or "dashboard" in self.driver.current_url:
                logger.info("WordPress login successful")
                self.is_logged_in = True
                return True
            else:
                logger.error("WordPress login failed - redirected to wrong page")
                return False
                
        except TimeoutException:
            logger.error("Timeout waiting for login page elements")
            return False
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def navigate_to_gis_admin(self) -> bool:
        """Navigate to GIS admin/devadmin page"""
        try:
            if not self.is_logged_in:
                logger.error("Not logged in to WordPress")
                return False
            
            logger.info("Navigating to GIS admin page...")
            self.driver.get(Config.GIS_ADMIN_URL)
            
            # Wait for page to load
            time.sleep(5)
            
            # Check if we're on the correct page
            if "devadmin" in self.driver.current_url or "gis" in self.driver.current_url.lower():
                logger.info("Successfully navigated to GIS admin page")
                return True
            else:
                logger.warning(f"May not be on correct GIS page. Current URL: {self.driver.current_url}")
                return True  # Continue anyway, might still work
                
        except Exception as e:
            logger.error(f"Failed to navigate to GIS admin: {str(e)}")
            return False
    
    def find_traffic_sign_element(self, image_path: str = None) -> Optional[Dict]:
        """Find traffic sign element on the map/page"""
        try:
            logger.info("Looking for traffic sign elements...")
            
            # This is a placeholder - you'll need to adapt this to your specific GIS interface
            # Common selectors for GIS interfaces:
            possible_selectors = [
                "//div[contains(@class, 'traffic-sign')]",
                "//div[contains(@class, 'sign')]", 
                "//div[contains(@class, 'marker')]",
                "//button[contains(text(), 'Traffic Sign')]",
                "//span[contains(text(), 'Sign')]"
            ]
            
            for selector in possible_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} potential traffic sign elements")
                        return {
                            'elements': elements,
                            'selector': selector,
                            'count': len(elements)
                        }
                except:
                    continue
            
            logger.warning("No traffic sign elements found with common selectors")
            return None
            
        except Exception as e:
            logger.error(f"Error finding traffic sign elements: {str(e)}")
            return None
    
    def fill_attribute_form(self, attributes: Dict[str, str]) -> bool:
        """Fill out the traffic sign attribute form"""
        try:
            logger.info("Filling attribute form...")
            
            success_count = 0
            total_attributes = len(attributes)
            
            for field_name, value in attributes.items():
                try:
                    # Try different methods to find and fill the field
                    success = self._fill_single_attribute(field_name, value)
                    if success:
                        success_count += 1
                        logger.info(f"Successfully filled {field_name}: {value}")
                    else:
                        logger.warning(f"Failed to fill {field_name}")
                        
                    time.sleep(0.5)  # Small delay between fills
                    
                except Exception as e:
                    logger.error(f"Error filling {field_name}: {str(e)}")
            
            logger.info(f"Form filling completed: {success_count}/{total_attributes} attributes filled")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error filling attribute form: {str(e)}")
            return False
    
    def _fill_single_attribute(self, field_name: str, value: str) -> bool:
        """Fill a single attribute field using multiple strategies"""
        strategies = [
            self._fill_by_name,
            self._fill_by_id,
            self._fill_by_label,
            self._fill_by_placeholder
        ]
        
        for strategy in strategies:
            try:
                if strategy(field_name, value):
                    return True
            except:
                continue
                
        return False
    
    def _fill_by_name(self, field_name: str, value: str) -> bool:
        """Fill field by name attribute"""
        try:
            element = self.driver.find_element(By.NAME, field_name)
            return self._fill_element(element, value)
        except:
            return False
    
    def _fill_by_id(self, field_name: str, value: str) -> bool:
        """Fill field by ID"""
        try:
            element = self.driver.find_element(By.ID, field_name)
            return self._fill_element(element, value)
        except:
            return False
    
    def _fill_by_label(self, field_name: str, value: str) -> bool:
        """Fill field by associated label"""
        try:
            label = self.driver.find_element(By.XPATH, f"//label[contains(text(), '{field_name}')]")
            field_id = label.get_attribute('for')
            if field_id:
                element = self.driver.find_element(By.ID, field_id)
                return self._fill_element(element, value)
        except:
            return False
    
    def _fill_by_placeholder(self, field_name: str, value: str) -> bool:
        """Fill field by placeholder text"""
        try:
            element = self.driver.find_element(By.XPATH, f"//input[@placeholder='{field_name}']")
            return self._fill_element(element, value)
        except:
            return False
    
    def _fill_element(self, element, value: str) -> bool:
        """Fill an element based on its type"""
        try:
            tag_name = element.tag_name.lower()
            element_type = element.get_attribute('type')
            
            if tag_name == 'select':
                # Handle dropdown/select
                select = Select(element)
                try:
                    select.select_by_visible_text(value)
                except:
                    select.select_by_value(value)
                return True
                
            elif element_type == 'checkbox':
                # Handle checkbox
                if value.lower() in ['true', '1', 'yes', 'checked']:
                    if not element.is_selected():
                        element.click()
                else:
                    if element.is_selected():
                        element.click()
                return True
                
            elif element_type == 'radio':
                # Handle radio button
                element.click()
                return True
                
            else:
                # Handle text input
                element.clear()
                element.send_keys(value)
                return True
                
        except Exception as e:
            logger.debug(f"Error filling element: {str(e)}")
            return False
    
    def save_form(self) -> bool:
        """Save/submit the form"""
        try:
            logger.info("Attempting to save form...")
            
            # Try different save button selectors
            save_selectors = [
                "//button[contains(text(), 'Save')]",
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//button[contains(text(), 'Update')]",
                "//button[contains(text(), 'Submit')]"
            ]
            
            for selector in save_selectors:
                try:
                    save_button = self.driver.find_element(By.XPATH, selector)
                    if save_button.is_displayed() and save_button.is_enabled():
                        save_button.click()
                        logger.info("Form saved successfully")
                        time.sleep(2)  # Wait for save to complete
                        return True
                except:
                    continue
            
            logger.warning("No save button found")
            return False
            
        except Exception as e:
            logger.error(f"Error saving form: {str(e)}")
            return False
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot for debugging"""
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            
            filepath = os.path.join("logs", filename)
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return ""
    
    def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
