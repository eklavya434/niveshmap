import os
import csv
from datetime import datetime
from src.ncr_intelligence.database.connection import engine, Base, get_db_session
from src.ncr_intelligence.database.models import DataSource, SourceAuditResult
from src.ncr_intelligence.ingestion.audit import SourceAuditor, load_sources_config

def generate_markdown_report(records: list, output_path: str):
    """Generates a human-readable markdown report from audit records."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    total = len(records)
    implemented = sum(1 for r in records if r["status"] == "implemented")
    partial = sum(1 for r in records if r["status"] == "partial")
    manual = sum(1 for r in records if r["status"] == "manual_download_required")
    blocked = sum(1 for r in records if r["status"] == "blocked")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Data Source Feasibility Audit Report\n\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"This report evaluates the feasibility of data acquisition from **{total}** critical public databases across the Delhi NCR region.\n\n")
        
        f.write("| Status | Count | Description |\n")
        f.write("| --- | --- | --- |\n")
        f.write(f"| **IMPLEMENTED** | {implemented} | Ready for automated ingestion (e.g. APIs, static endpoints) |\n")
        f.write(f"| **PARTIAL** | {partial} | Semi-automated extraction implemented |\n")
        f.write(f"| **MANUAL DOWNLOAD REQUIRED** | {manual} | Protected by CAPTCHAs, bot blocks, or multi-step form submissions |\n")
        f.write(f"| **BLOCKED** | {blocked} | Restricted access or legally constrained sources |\n\n")
        
        f.write("> [!NOTE]\n")
        f.write("> RERA portals and circle rates frequently fall into `MANUAL_DOWNLOAD_REQUIRED` due to CAPTCHA protections and PDF-only distribution formats. This project builds reproducible manual adapters rather than bypassing security mechanisms.\n\n")
        
        f.write("## Detailed Source Audit Registry\n\n")
        f.write("| Source ID | Source Name | Geography | Category | Format | Access Method | Feasibility | Status | Notes |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        
        for r in records:
            # Shorten notes for table readability
            note_summary = r["notes"].replace("\n", " ")
            if len(note_summary) > 100:
                note_summary = note_summary[:97] + "..."
            
            f.write(f"| `{r['source_id']}` | {r['source_name']} | {r['geography']} | {r['source_category']} | {r['expected_format'].upper()} | {r['access_method']} | {r['automation_feasibility']} | **{r['status'].upper()}** | {note_summary} |\n")
            
        f.write("\n## Feasibility Analysis & Recommendations\n\n")
        f.write("### 1. Real Estate Price Data (The Price Proxy Problem)\n")
        f.write("- **Circle Rates**: High manual intervention is required. PDFs must be periodically downloaded per district (Noida, Gurugram, Delhi) and compiled into spatial lookup tables.\n")
        f.write("- **RERA Filings**: Excellent for project details, but bulk price details are locked behind JS grids or CAPTCHAs. Recommended approach: compile raw data from manual quarterly downloads or sample RERA filings to construct composite project price proxies.\n")
        f.write("- **NHB RESIDEX**: Reliable regional HPI trends are available in Excel format. This will serve as our quarterly baseline normalization index.\n\n")
        
        f.write("### 2. Infrastructure Project Milestones\n")
        f.write("- **DMRC/NMRC/NCRTC**: General timelines are obtainable via press releases and official site histories. PIB is highly valuable as a structured text feed for timeline reconstruction (cabinet approval, funding, construction start, commissioning dates).\n")
        
    print(f"Markdown report generated: {output_path}")


def main():
    print("====================================================")
    print("RUNNING NCR REAL ESTATE DATA SOURCE FEASIBILITY AUDIT")
    print("====================================================")
    
    # 1. Initialize tables
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Load configurations
    sources = load_sources_config()
    if not sources:
        print("Error: No sources found in config/sources.yaml.")
        return
        
    db = get_db_session()
    try:
        # Populate data sources metadata
        print(f"Registering {len(sources)} data sources...")
        for src_conf in sources:
            db_source = db.query(DataSource).filter_by(source_id=src_conf["source_id"]).first()
            if not db_source:
                db_source = DataSource(
                    source_id=src_conf["source_id"],
                    source_name=src_conf["source_name"],
                    source_category=src_conf["source_category"],
                    geography=src_conf["geography"],
                    official_source=src_conf.get("official_source", True),
                    source_url=src_conf.get("source_url"),
                    access_method=src_conf["access_method"],
                    expected_format=src_conf["expected_format"],
                    historical_depth_notes=src_conf.get("historical_depth_notes"),
                    legal_access_notes=src_conf.get("legal_access_notes"),
                    active=src_conf.get("active", True)
                )
                db.add(db_source)
            else:
                db_source.source_name = src_conf["source_name"]
                db_source.source_category = src_conf["source_category"]
                db_source.geography = src_conf["geography"]
                db_source.official_source = src_conf.get("official_source", True)
                db_source.source_url = src_conf.get("source_url")
                db_source.access_method = src_conf["access_method"]
                db_source.expected_format = src_conf["expected_format"]
                db_source.historical_depth_notes = src_conf.get("historical_depth_notes")
                db_source.legal_access_notes = src_conf.get("legal_access_notes")
                db_source.active = src_conf.get("active", True)
        db.commit()
        
        # 3. Run audit
        auditor = SourceAuditor(sources)
        audit_records = auditor.audit_all()
        
        # Write CSV output
        csv_path = "data/processed/source_audit.csv"
        auditor.write_results_csv(audit_records, csv_path)
        print(f"CSV output saved to: {csv_path}")
        
        # Save audit results inside SQLite db
        print("Writing audit records to DB...")
        # Clear previous audits to prevent duplicates in local sqlite run
        db.query(SourceAuditResult).delete()
        
        for rec in audit_records:
            earliest = None
            if rec["earliest_date_found"] and rec["earliest_date_found"] != "None":
                earliest = datetime.strptime(rec["earliest_date_found"], "%Y-%m-%d").date()
            latest = None
            if rec["latest_date_found"] and rec["latest_date_found"] != "None":
                latest = datetime.strptime(rec["latest_date_found"], "%Y-%m-%d").date()
                
            db_audit = SourceAuditResult(
                source_id=rec["source_id"],
                accessible=True if rec["accessibility"] == "PUBLIC" else False,
                records_found=rec["records_found"],
                earliest_date_found=earliest,
                latest_date_found=latest,
                structured_data_available=rec["structured_data_available"],
                manual_intervention_required=rec["manual_intervention_required"],
                notes=rec["notes"]
            )
            db.add(db_audit)
        db.commit()
        
        # 4. Write MD report
        md_path = "reports/phase0/source_audit.md"
        generate_markdown_report(audit_records, md_path)
        
        print("Source feasibility audit run completed successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error occurred during audit run: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
