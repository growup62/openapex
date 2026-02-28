import logging
import argparse
import os
import time
from orchestrator.brain import Brain
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="openApex Cognitive Agent System V4")
    parser.add_argument('--telegram', action='store_true', help='Enable Telegram bot interface')
    parser.add_argument('--whatsapp', action='store_true', help='Enable WhatsApp bridge interface')
    parser.add_argument('--autonomous', action='store_true', help='Enable full autonomous mode (AI runs by itself)')
    parser.add_argument('--interval', type=int, default=60, help='Autonomous cycle interval in seconds (default: 60)')
    args = parser.parse_args()
    
    # Ensure API key is present
    if not os.getenv("OPENROUTER_API_KEY"):
         print("CRITICAL: OPENROUTER_API_KEY is missing from .env File.")
         print("Please add your key to proceed.")
         return
         
    print("==============================================")
    print("  Welcome to openApex Cognitive Agent System")
    print("       V4 — Fully Autonomous Intelligence")
    print("==============================================")

    # Initialize the core brain
    apex_brain = Brain()
    
    # Start Telegram bot if requested
    if args.telegram:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("[ERROR]: TELEGRAM_BOT_TOKEN not found in .env file!")
        else:
            try:
                from interfaces.telegram_bot import TelegramBot
                telegram = TelegramBot(token=token, brain_instance=apex_brain)
                telegram.run_in_background()
                print("[System]: 🤖 Telegram Bot started in background!")
            except ImportError as e:
                print(f"[ERROR]: Could not start Telegram bot: {e}")
                print("         Run: pip install python-telegram-bot")
    
    # Start WhatsApp bridge if requested
    if args.whatsapp:
        try:
            from interfaces.whatsapp_client import WhatsAppClient
            wa_client = WhatsAppClient(brain_instance=apex_brain)
            wa_client.run_in_background()
            print("[System]: 💬 WhatsApp backend started!")
            print("[System]: Run 'cd interfaces/whatsapp_bridge && npm install && npm start' in another terminal.")
        except Exception as e:
            print(f"[ERROR]: Could not start WhatsApp bridge: {e}")
    
    # Start autonomous daemon if requested
    autonomy = None
    if args.autonomous:
        from core.autonomy import AutonomyEngine
        autonomy = AutonomyEngine(brain_instance=apex_brain)
        autonomy.cycle_interval = args.interval
        autonomy.start()
    
    # Show active interfaces
    active = ["Terminal"]
    if args.telegram:
        active.append("Telegram")
    if args.whatsapp:
        active.append("WhatsApp")
    if args.autonomous:
        active.append("Autonomous 🤖")
    print(f"\n[Active interfaces: {', '.join(active)}]")
    
    if args.autonomous:
        print("[Mode: AUTONOMOUS — openApex berjalan sendiri, ketik perintah atau 'exit' untuk berhenti]")
    
    print("[System initialized. Type 'exit' to quit]\n")
    
    while True:
        try:
            user_input = input("You> ")
            if user_input.lower() in ['exit', 'quit']:
                if autonomy:
                    autonomy.stop()
                break
            
            if user_input.lower() == 'status':
                if autonomy:
                    status = autonomy.get_status()
                    print(f"\n🤖 Autonomous Status:")
                    print(f"   Running: {status['running']}")
                    print(f"   Mode: {status['mode']}")
                    print(f"   Cycles: {status['cycle_count']}")
                    print(f"   Interval: {status['cycle_interval_seconds']}s\n")
                if hasattr(apex_brain, 'consciousness'):
                    intro = apex_brain.consciousness.introspect()
                    print(f"🧠 Consciousness:")
                    print(f"   Mood: {intro['mood']}")
                    print(f"   Confidence: {intro['confidence']}")
                    print(f"   Tasks completed: {intro['tasks_completed_this_session']}\n")
                continue
                
            if not user_input.strip():
                continue
                
            print("openApex> Let me think about that...")
            
            # Initiate the cognitive execution loop
            apex_brain.solve(user_input)
            
            print("openApex> Finished current task cycle.")

        except EOFError:
            print("[System]: Non-interactive environment detected. Switching to passive mode.")
            print("[System]: openApex will continue to run interfaces and autonomous cycles.")
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nExiting openApex...")
            if autonomy:
                autonomy.stop()
            break
        except Exception as e:
            logger.error(f"Fatal error in execution loop: {e}")
            break

if __name__ == "__main__":
    main()
