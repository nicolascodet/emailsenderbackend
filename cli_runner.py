"""
CLI Runner for the AI Outreach Pipeline
"""
import asyncio
import sys
from outreach_pipeline import OutreachPipeline

async def main():
    try:
        print("🚀 AI Outreach Pipeline - Multi-Agent Email Sniper")
        print("=" * 60)
        print("This system will:")
        print("1. 🔍 Scrape LinkedIn profiles and classify personality types")
        print("2. 🌐 Analyze company websites for business intelligence")
        print("3. 🎯 Match your best service offering to each prospect")
        print("4. 📋 Select the optimal Reddit-proven outreach strategy")
        print("5. ✍️  Generate personalized messages")
        print("6. 📧 Send emails via Gmail SMTP with rate limiting")
        print("=" * 60)
        
        # Initialize pipeline
        pipeline = OutreachPipeline()
        
        # Get input format preference
        print("\nInput Options:")
        print("1. CSV format (recommended)")
        print("2. Manual input (tab or comma separated)")
        
        while True:
            choice = input("\nSelect input format (1 or 2): ").strip()
            if choice in ['1', '2']:
                break
            print("Please enter 1 or 2")
        
        if choice == '1':
            print("\n📋 CSV Input Format:")
            print("Expected columns: Name, Email, LinkedIn URL, Company Domain, Phone")
            print("(LinkedIn URL, Company Domain, and Phone are optional)")
            print("\nPaste your CSV data below, then press Enter and Ctrl+D (Cmd+D on Mac):")
            
            csv_data = ""
            try:
                while True:
                    line = input()
                    csv_data += line + "\n"
            except EOFError:
                pass
            
            prospects = pipeline.parse_csv_input(csv_data)
            
        else:
            print("\n📋 Manual Input Format:")
            print("Format: Name, Email, LinkedIn URL, Company Domain, Phone")
            print("(One prospect per line, comma or tab separated)")
            print("Minimum required: Name, Email")
            print("\nPaste your data below, then press Enter and Ctrl+D (Cmd+D on Mac):")
            
            manual_data = ""
            try:
                while True:
                    line = input()
                    manual_data += line + "\n"
            except EOFError:
                pass
            
            prospects = pipeline.parse_manual_input(manual_data)
        
        if not prospects:
            print("❌ No valid prospects found. Please check your input format and try again.")
            return
        
        print(f"\n✅ Found {len(prospects)} valid prospects")
        
        # Show what we're about to do
        print(f"\n🎯 Ready to process prospects:")
        for i, prospect in enumerate(prospects[:5], 1):  # Show first 5
            print(f"   {i}. {prospect.name} ({prospect.email})")
        if len(prospects) > 5:
            print(f"   ... and {len(prospects) - 5} more")
        
        # Confirm before proceeding
        confirm = input(f"\nProceed with processing {len(prospects)} prospects? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
        
        # Process prospects
        print(f"\n🚀 Starting pipeline processing...")
        results = await pipeline.process_prospects(prospects)
        
        # Show final results
        print(f"\n" + "=" * 60)
        print("📊 FINAL RESULTS")
        print("=" * 60)
        
        successful = [r for r in results if r.sent]
        failed = [r for r in results if not r.sent]
        
        print(f"✅ Successfully sent: {len(successful)} emails")
        print(f"❌ Failed to send: {len(failed)} emails")
        
        if failed:
            print(f"\n❌ Failed prospects:")
            for result in failed:
                print(f"   • {result.prospect.name}: {result.error}")
        
        if successful:
            print(f"\n✅ Successful sends:")
            for result in successful:
                print(f"   • {result.prospect.name} ({result.prospect.email})")
                if result.message:
                    print(f"     Strategy: {result.message.strategy.value}")
                    print(f"     Offer: {result.message.selected_offer.name}")
        
        print(f"\n🎉 Pipeline complete! Check your email tracking for deliverability.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 