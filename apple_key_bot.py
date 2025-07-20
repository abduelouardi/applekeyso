import asyncio
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import os
import time
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
TELEGRAM_TOKEN = "7623137573:AAEHiRKpuG1T77cP6hWgyx_bai-G9IuP-0o"
BASE_URL = "https://redeem.services.apple/card-apple-entertainment-offer-1-2025"

# Service configurations
SERVICES = {
    "tv": {
        "name": "🍎 Apple TV+",
        "xpath": '/html/body/div[1]/main/div/div[1]/div/div/div/div[1]/div[1]/div/div[2]/button',
        "domain": "tv.apple.com"
    },
    "music": {
        "name": "🎵 Apple Music",
        "xpath": '/html/body/div[1]/main/div/div[1]/div/div/div/div[1]/div[2]/div/div[2]/button',
        "domain": "music.apple.com"
    },
    "arcade": {
        "name": "🕹️ Apple Arcade",
        "xpath": '/html/body/div[1]/main/div/div[1]/div/div/div/div[1]/div[3]/div/div[2]/button',
        "domain": "arcade.apple.com"
    },
    "fitness": {
        "name": "💪 Apple Fitness+",
        "xpath": '/html/body/div[1]/main/div/div[1]/div/div/div/div[1]/div[4]/div/div[2]/button',
        "domain": "fitness.apple.com"
    },
    "news": {
        "name": "📰 Apple News+",
        "xpath": '/html/body/div[1]/main/div/div[1]/div/div/div/div[1]/div[5]/div/div[2]/button',
        "domain": "news.apple.com"
    }
}

class AppleKeyGenerator:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with privacy settings"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Auto-install ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome driver setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return False
    
    def generate_key(self, service_name):
        """Generate key for specific Apple service"""
        if not self.setup_driver():
            return None, "Failed to setup browser"
            
        try:
            service_config = SERVICES.get(service_name)
            if not service_config:
                return None, f"Service '{service_name}' not found"
            
            # Navigate to base URL
            self.driver.get(BASE_URL)
            wait = WebDriverWait(self.driver, 15)
            
            # Wait for page to load and click service button
            button = wait.until(EC.element_to_be_clickable((By.XPATH, service_config["xpath"])))
            time.sleep(random.uniform(1, 3))  # Random delay
            button.click()
            
            # Wait for redirect and extract key from URL
            wait.until(lambda driver: service_config["domain"] in driver.current_url)
            current_url = self.driver.current_url
            
            # Extract key using regex
            key_match = re.search(r'[?&]code=([A-Z0-9]+)', current_url)
            if key_match:
                key = key_match.group(1)
                logger.info(f"Generated {service_name} key: {key}")
                return key, "Success"
            else:
                logger.error(f"Could not extract key from URL: {current_url}")
                return None, "Failed to extract key from URL"
                
        except TimeoutException:
            logger.error("Timeout while generating key")
            return None, "Timeout - page took too long to load"
        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            return None, f"Browser error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None, f"Unexpected error: {str(e)}"
        finally:
            if self.driver:
                self.driver.quit()

# Global key generator instance
key_generator = AppleKeyGenerator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_message = """
🍎 **Apple Key Generator Bot** 🍎

Welcome! I can generate promo keys for Apple services.

Available services:
🍎 Apple TV+
🎵 Apple Music  
🕹️ Apple Arcade
💪 Apple Fitness+
📰 Apple News+

Use /generate to get started or click the button below!
"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 Generate Keys", callback_data="generate_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def generate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show service selection menu"""
    keyboard = []
    
    # Add service buttons (2 per row)
    service_buttons = []
    for service_id, service_info in SERVICES.items():
        service_buttons.append(
            InlineKeyboardButton(service_info["name"], callback_data=f"gen_{service_id}")
        )
    
    # Arrange in rows of 2
    for i in range(0, len(service_buttons), 2):
        row = service_buttons[i:i+2]
        keyboard.append(row)
    
    # Add generate all button
    keyboard.append([InlineKeyboardButton("🎯 Generate All Keys", callback_data="gen_all")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = """
🎯 **Select Apple Service**

Choose which service key you want to generate:

⚡ Single service generation
🎯 Or generate all keys at once

*Note: Key generation may take 15-30 seconds per service*
"""
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def generate_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle key generation requests"""
    query = update.callback_query
    await query.answer()
    
    # Show loading message
    loading_msg = await query.edit_message_text("🔄 Generating key(s)... Please wait...")
    
    if query.data == "gen_all":
        # Generate all keys
        results = []
        total_services = len(SERVICES)
        
        for i, (service_id, service_info) in enumerate(SERVICES.items(), 1):
            # Update progress
            await loading_msg.edit_text(
                f"🔄 Generating keys... ({i}/{total_services})\n"
                f"Currently processing: {service_info['name']}"
            )
            
            key, status = key_generator.generate_key(service_id)
            results.append({
                'service': service_info['name'],
                'key': key,
                'status': status
            })
            
            # Small delay between requests
            await asyncio.sleep(2)
        
        # Format results
        result_text = "🎯 **All Keys Generation Results:**\n\n"
        successful_keys = 0
        
        for result in results:
            if result['key']:
                result_text += f"✅ {result['service']}: `{result['key']}`\n"
                successful_keys += 1
            else:
                result_text += f"❌ {result['service']}: {result['status']}\n"
        
        result_text += f"\n📊 **Summary:** {successful_keys}/{len(SERVICES)} keys generated successfully"
        
    else:
        # Generate single key
        service_id = query.data.replace("gen_", "")
        service_info = SERVICES.get(service_id)
        
        if not service_info:
            await loading_msg.edit_text("❌ Invalid service selected")
            return
        
        key, status = key_generator.generate_key(service_id)
        
        if key:
            result_text = f"✅ **{service_info['name']} Key Generated!**\n\n"
            result_text += f"🔑 Key: `{key}`\n"
            result_text += f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            result_text = f"❌ **Failed to generate {service_info['name']} key**\n\n"
            result_text += f"Error: {status}"
    
    # Add back button
    keyboard = [
        [InlineKeyboardButton("🔄 Generate Again", callback_data="generate_menu")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await loading_msg.edit_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    
    if query.data == "generate_menu":
        await generate_menu(update, context)
    elif query.data == "back_menu":
        await start_menu(update, context)
    elif query.data.startswith("gen_"):
        await generate_key_handler(update, context)

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to start menu"""
    welcome_message = """
🍎 **Apple Key Generator Bot** 🍎

Welcome! I can generate promo keys for Apple services.

Available services:
🍎 Apple TV+
🎵 Apple Music  
🕹️ Apple Arcade
💪 Apple Fitness+
📰 Apple News+

Use /generate to get started or click the button below!
"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 Generate Keys", callback_data="generate_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
🍎 **Apple Key Generator Bot - Help**

**Available Commands:**
/start - Start the bot
/generate - Open key generation menu  
/help - Show this help message
/status - Check bot status

**How it works:**
1. Click "Generate Keys" 
2. Select a service or generate all
3. Wait for key generation (15-30 sec per key)
4. Copy your generated key

**Supported Services:**
🍎 Apple TV+ 
🎵 Apple Music
🕹️ Apple Arcade  
💪 Apple Fitness+
📰 Apple News+

**Notes:**
- Keys are generated in real-time
- Each generation creates a fresh private session
- Keys are valid for redemption on Apple services

Need help? Contact support!
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command handler"""
    status_text = f"""
📊 **Bot Status**

🤖 Bot: Online ✅
🕐 Uptime: Active
🔧 Services: {len(SERVICES)} available
🌐 Chrome Driver: Auto-managed
📱 Telegram API: Connected

**System Info:**
- Headless browsing: Enabled
- Private sessions: Enabled  
- Auto key extraction: Enabled

Bot is ready to generate Apple service keys! 🚀
"""
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

def main():
    """Main function to run the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", generate_menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Run the bot
    logger.info("Starting Apple Key Generator Bot...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
