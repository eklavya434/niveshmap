import os
from datetime import datetime, date
from src.ncr_intelligence.database.connection import Base, engine, get_db_session
from src.ncr_intelligence.database.models import PropertyPriceObservation, InfrastructureProject, InfrastructureEvent
from src.ncr_intelligence.utils.validation import PriceObservationValidator, InfrastructureProjectValidator, InfrastructureEventValidator

# Import Ingestion Adapters
from src.ncr_intelligence.ingestion.nhb import NHBResidexAdapter
from src.ncr_intelligence.ingestion.rera.up_rera import UPRERAAdapter
from src.ncr_intelligence.ingestion.rera.hrera import HRERAAdapter
from src.ncr_intelligence.ingestion.rera.delhi_rera import DelhiRERAAdapter
from src.ncr_intelligence.ingestion.circle_rates.up import UPCircleRatesAdapter
from src.ncr_intelligence.ingestion.circle_rates.haryana import HaryanaCollectorRatesAdapter
from src.ncr_intelligence.ingestion.circle_rates.delhi import DelhiCircleRatesAdapter
from src.ncr_intelligence.ingestion.infrastructure.pib import PIBAdapter
from src.ncr_intelligence.ingestion.infrastructure.authorities import TransitAuthoritiesAdapter

def collect_all_sources():
    print("====================================================")
    print("RUNNING NCR REAL ESTATE PIPELINE INGESTION ORCHESTRATOR")
    print("====================================================")
    
    # 1. Initialize tables (ensure schema is loaded)
    Base.metadata.create_all(bind=engine)
    
    db = get_db_session()
    try:
        # Clear previous rows to avoid duplicates during raw collection runs
        db.query(PropertyPriceObservation).delete()
        db.query(InfrastructureEvent).delete()
        db.query(InfrastructureProject).delete()
        db.commit()
        
        # ----------------------------------------------------
        # 1. INGEST NHB RESIDEX BASELINE
        # ----------------------------------------------------
        nhb_path = "data/sample/nhb_residex.csv"
        if os.path.exists(nhb_path):
            print(f"Parsing NHB index from: {nhb_path}")
            adapter = NHBResidexAdapter({"source_id": "nhb_residex"})
            records = adapter.parse_index(nhb_path)
            
            # Map index cities to specific localities to test baseline linkages
            city_localities = {
                "Delhi": ["DEL_DWR_SEC10", "DEL_VK_SEC_A"],
                "Noida": ["NOI_SEC62", "NOI_SEC150", "GNW_SEC4", "GNW_SEC1"],
                "Gurugram": ["GUR_DLF3", "GUR_SEC82"]
            }
            
            obs_count = 0
            for rec in records:
                localities = city_localities.get(rec["city"], [])
                for loc_id in localities:
                    # Validate price observation
                    val_data = {
                        "locality_id": loc_id,
                        "observation_date": date(2019, 1, 1), # Default proxy date
                        "quarter": rec["quarter"],
                        "price_value": rec["index_value"],
                        "price_unit": "index_ratio",
                        "price_type": "index",
                        "source_id": "nhb_residex",
                        "source_quality_class": "HIGH",
                        "is_proxy": True,
                        "raw_reference": f"NHB Residex HPI for {rec['city']}"
                    }
                    validator = PriceObservationValidator(**val_data)
                    
                    # Convert to DB Model
                    db_obs = PropertyPriceObservation(
                        locality_id=validator.locality_id,
                        observation_date=validator.observation_date,
                        quarter=validator.quarter,
                        price_value=validator.price_value,
                        price_unit=validator.price_unit,
                        price_type=validator.price_type,
                        source_id=validator.source_id,
                        source_quality_class=validator.source_quality_class,
                        is_proxy=validator.is_proxy,
                        raw_reference=validator.raw_reference
                    )
                    db.add(db_obs)
                    obs_count += 1
            print(f"Successfully loaded {obs_count} NHB index observations.")
            
        # ----------------------------------------------------
        # 2. INGEST CIRCLE RATES
        # ----------------------------------------------------
        # UP Circle rates
        up_circle_path = "data/sample/up_circle_rates.csv"
        if os.path.exists(up_circle_path):
            print(f"Parsing UP Circle rates from: {up_circle_path}")
            adapter = UPCircleRatesAdapter({"source_id": "up_circle_rates"})
            records = adapter.parse_rates(up_circle_path)
            for rec in records:
                # Map UP locality keys directly
                val_data = {
                    "locality_id": rec["locality_key"],
                    "observation_date": datetime.strptime(rec["effective_date"], "%Y-%m-%d").date(),
                    "quarter": "2019-Q3",
                    "price_value": rec["circle_rate"],
                    "price_unit": rec["unit"],
                    "price_type": "circle_rate",
                    "source_id": "up_circle_rates",
                    "source_quality_class": "HIGH",
                    "is_proxy": False,
                    "raw_reference": f"UP Circle Rate Gazette {rec['effective_date']}"
                }
                validator = PriceObservationValidator(**val_data)
                db_obs = PropertyPriceObservation(**validator.model_dump())
                db.add(db_obs)
                
        # Haryana Collector rates
        hr_circle_path = "data/sample/hparams_collector_rates.csv" # wait, the file created was haryana_collector_rates.csv
        if not os.path.exists(hr_circle_path):
            hr_circle_path = "data/sample/haryana_collector_rates.csv"
            
        if os.path.exists(hr_circle_path):
            print(f"Parsing Haryana Collector rates from: {hr_circle_path}")
            adapter = HaryanaCollectorRatesAdapter({"source_id": "haryana_collector_rates"})
            records = adapter.parse_rates(hr_circle_path)
            for rec in records:
                val_data = {
                    "locality_id": rec["locality_key"],
                    "observation_date": datetime.strptime(rec["effective_date"], "%Y-%m-%d").date(),
                    "quarter": "2020-Q2",
                    "price_value": rec["collector_rate"],
                    "price_unit": rec["unit"],
                    "price_type": "circle_rate",
                    "source_id": "haryana_collector_rates",
                    "source_quality_class": "HIGH",
                    "is_proxy": False,
                    "raw_reference": f"Haryana Collector Rate notification {rec['effective_date']}"
                }
                validator = PriceObservationValidator(**val_data)
                db_obs = PropertyPriceObservation(**validator.model_dump())
                db.add(db_obs)
                
        # Delhi Circle rates
        del_circle_path = "data/sample/delhi_circle_rates.csv"
        if os.path.exists(del_circle_path):
            print(f"Parsing Delhi Circle rates from: {del_circle_path}")
            adapter = DelhiCircleRatesAdapter({"source_id": "delhi_circle_rates"})
            records = adapter.parse_rates(del_circle_path)
            
            # Extract category maps for Delhi localities
            delhi_locs = ["DEL_DWR_SEC10", "DEL_VK_SEC_A"]
            for loc_id in delhi_locs:
                mapped_rate = adapter.get_rate_for_locality(records, loc_id)
                val_data = {
                    "locality_id": loc_id,
                    "observation_date": datetime.strptime(mapped_rate["effective_date"], "%Y-%m-%d").date(),
                    "quarter": "2014-Q4",
                    "price_value": mapped_rate["circle_rate"],
                    "price_unit": mapped_rate["unit"],
                    "price_type": "circle_rate",
                    "source_id": "delhi_circle_rates",
                    "source_quality_class": "HIGH",
                    "is_proxy": False,
                    "raw_reference": f"Delhi Circle Rate class classification Category {mapped_rate['category']}"
                }
                validator = PriceObservationValidator(**val_data)
                db_obs = PropertyPriceObservation(**validator.model_dump())
                db.add(db_obs)
                
        # ----------------------------------------------------
        # 3. INGEST RERA DEVELOPMENTS
        # ----------------------------------------------------
        # UP RERA
        up_rera_path = "data/sample/up_rera.json"
        if os.path.exists(up_rera_path):
            print(f"Parsing UP RERA disclosures from: {up_rera_path}")
            adapter = UPRERAAdapter({"source_id": "up_rera"})
            records = adapter.parse_projects(up_rera_path)
            for rec in records:
                norm = adapter.normalize_project(rec)
                
                # Check if price is available
                if norm["price_value"] > 0.0:
                    val_data = {
                        "locality_id": "NOI_SEC150", # Associated sample locality Noida Extension
                        "observation_date": date(2018, 6, 15),
                        "quarter": "2018-Q2",
                        "price_value": norm["price_value"],
                        "price_unit": norm["price_unit"],
                        "price_type": "rera_disclosure",
                        "source_id": "up_rera",
                        "source_quality_class": "MEDIUM",
                        "is_proxy": False,
                        "raw_reference": norm["raw_reference"]
                    }
                    validator = PriceObservationValidator(**val_data)
                    db_obs = PropertyPriceObservation(**validator.model_dump())
                    db.add(db_obs)
                    
        # ----------------------------------------------------
        # 4. INGEST TRANSIT & PIB INFRASTRUCTURE
        # ----------------------------------------------------
        # Transit authority projects
        transit_path = "data/sample/transit_events.json"
        if os.path.exists(transit_path):
            print(f"Parsing transit events from: {transit_path}")
            adapter = TransitAuthoritiesAdapter({"source_id": "dmrc_metro"})
            records = adapter.parse_events(transit_path)
            
            for rec in records:
                # Validate project
                proj_val = {
                    "project_id": rec["project_id"],
                    "project_name": rec["project_name"],
                    "normalized_name": rec["normalized_name"],
                    "project_type": rec["project_type"],
                    "primary_authority": rec["primary_authority"],
                    "current_stage": rec["stage"]
                }
                validator_proj = InfrastructureProjectValidator(**proj_val)
                
                # Save project
                db_proj = db.query(InfrastructureProject).filter_by(project_id=validator_proj.project_id).first()
                if not db_proj:
                    db_proj = InfrastructureProject(
                        project_id=validator_proj.project_id,
                        project_name=validator_proj.project_name,
                        normalized_name=validator_proj.normalized_name,
                        project_type=validator_proj.project_type,
                        primary_authority=validator_proj.primary_authority,
                        current_stage=validator_proj.current_stage
                    )
                    db.add(db_proj)
                db.commit()
                
                # Save event
                evt_val = {
                    "project_id": rec["project_id"],
                    "stage": rec["stage"],
                    "raw_stage_text": rec["raw_stage_text"],
                    "event_date": rec["event_date"],
                    "article_publish_date": rec["article_publish_date"],
                    "evidence_source_id": "dmrc_metro",
                    "evidence_strength": rec["evidence_strength"],
                    "evidence_phrase": rec["evidence_phrase"]
                }
                validator_evt = InfrastructureEventValidator(**evt_val)
                
                db_evt = InfrastructureEvent(
                    project_id=validator_evt.project_id,
                    stage=validator_evt.stage,
                    raw_stage_text=validator_evt.raw_stage_text,
                    event_date=validator_evt.event_date,
                    article_publish_date=validator_evt.article_publish_date,
                    evidence_source_id=validator_evt.evidence_source_id,
                    evidence_strength=validator_evt.evidence_strength,
                    evidence_phrase=validator_evt.evidence_phrase
                )
                db.add(db_evt)
                
        db.commit()
        print("Data collection and validation pipeline execution finished successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Pipeline collection failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    collect_all_sources()
