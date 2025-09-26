#!/usr/bin/env python3
"""
🗄️ LOCAL AI DATABASE SYSTEM
============================
Advanced local database for storing, managing, and learning from holder analysis data.
Provides consistent accuracy without relying on external APIs.

Features:
- SQLite-based local storage
- Hash-based photo management
- Learning from corrections
- Accuracy tracking and improvement
- Boss system integration ready
- Compatible with existing SmartMap workflow
"""

import sqlite3
import json
import time
import hashlib
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path

@dataclass
class HolderAnalysis:
    """Data class for holder analysis results"""
    holder_id: str
    material: str
    holder_type: str
    confidence: float
    photo_hash: Optional[str] = None
    analysis_method: str = "local_ai"
    timestamp: float = 0.0
    verified: bool = False
    correction_count: int = 0
    photo_path: Optional[str] = None

class LocalAIDatabase:
    """Local AI database for holder analysis management"""
    
    def __init__(self, db_path: str = "local_holder_ai.db"):
        self.db_path = db_path
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        """Setup logging for database operations"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("LocalAIDB")
        
    def setup_database(self):
        """Initialize the local database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holder_analysis (
                holder_id TEXT PRIMARY KEY,
                material TEXT NOT NULL,
                holder_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                photo_hash TEXT,
                analysis_method TEXT NOT NULL,
                timestamp REAL NOT NULL,
                verified BOOLEAN DEFAULT FALSE,
                correction_count INTEGER DEFAULT 0,
                photo_path TEXT,
                notes TEXT
            )
        ''')
        
        # Accuracy tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accuracy_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holder_id TEXT,
                original_material TEXT,
                original_type TEXT,
                corrected_material TEXT,
                corrected_type TEXT,
                analysis_method TEXT,
                correction_timestamp REAL,
                FOREIGN KEY (holder_id) REFERENCES holder_analysis (holder_id)
            )
        ''')
        
        # Pattern learning table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_value TEXT,
                predicted_material TEXT,
                predicted_type TEXT,
                success_rate REAL,
                sample_count INTEGER,
                last_updated REAL
            )
        ''')
        
        # Photo management table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photo_management (
                photo_hash TEXT PRIMARY KEY,
                holder_id TEXT,
                file_path TEXT,
                file_size INTEGER,
                photo_timestamp REAL,
                analysis_count INTEGER DEFAULT 0,
                FOREIGN KEY (holder_id) REFERENCES holder_analysis (holder_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("✅ Local AI database initialized")
        
    def store_analysis(self, analysis: HolderAnalysis) -> bool:
        """Store analysis result in local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO holder_analysis 
                (holder_id, material, holder_type, confidence, photo_hash, 
                 analysis_method, timestamp, verified, correction_count, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis.holder_id,
                analysis.material,
                analysis.holder_type,
                analysis.confidence,
                analysis.photo_hash,
                analysis.analysis_method,
                analysis.timestamp or time.time(),
                analysis.verified,
                analysis.correction_count,
                analysis.photo_path
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Stored analysis for holder {analysis.holder_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store analysis: {e}")
            return False
            
    def get_analysis(self, holder_id: str) -> Optional[HolderAnalysis]:
        """Retrieve analysis result for a holder"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT holder_id, material, holder_type, confidence, photo_hash,
                       analysis_method, timestamp, verified, correction_count, photo_path
                FROM holder_analysis WHERE holder_id = ?
            ''', (holder_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return HolderAnalysis(
                    holder_id=result[0],
                    material=result[1],
                    holder_type=result[2],
                    confidence=result[3],
                    photo_hash=result[4],
                    analysis_method=result[5],
                    timestamp=result[6],
                    verified=bool(result[7]),
                    correction_count=result[8],
                    photo_path=result[9]
                )
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve analysis: {e}")
            return None
            
    def update_with_correction(self, holder_id: str, corrected_material: str, corrected_type: str) -> bool:
        """Update analysis with manual correction and learn from it"""
        try:
            # Get current analysis
            current = self.get_analysis(holder_id)
            if not current:
                return False
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store the correction in accuracy tracking
            cursor.execute('''
                INSERT INTO accuracy_tracking 
                (holder_id, original_material, original_type, corrected_material, 
                 corrected_type, analysis_method, correction_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                holder_id,
                current.material,
                current.holder_type,
                corrected_material,
                corrected_type,
                current.analysis_method,
                time.time()
            ))
            
            # Update the main analysis record
            cursor.execute('''
                UPDATE holder_analysis 
                SET material = ?, holder_type = ?, verified = TRUE, 
                    correction_count = correction_count + 1
                WHERE holder_id = ?
            ''', (corrected_material, corrected_type, holder_id))
            
            conn.commit()
            conn.close()
            
            # Update pattern learning
            self._update_pattern_learning(holder_id, corrected_material, corrected_type)
            
            self.logger.info(f"✅ Updated holder {holder_id} with correction")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update with correction: {e}")
            return False
            
    def _update_pattern_learning(self, holder_id: str, material: str, holder_type: str):
        """Update pattern learning based on corrections"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Learn from holder ID patterns
            try:
                holder_num = int(holder_id)
                patterns = [
                    ("id_mod_10", str(holder_num % 10)),
                    ("id_mod_15", str(holder_num % 15)),
                    ("id_mod_20", str(holder_num % 20)),
                    ("id_range_100", str(holder_num // 100)),
                    ("id_range_50", str(holder_num // 50))
                ]
                
                for pattern_type, pattern_value in patterns:
                    cursor.execute('''
                        INSERT OR IGNORE INTO pattern_learning 
                        (pattern_type, pattern_value, predicted_material, predicted_type, 
                         success_rate, sample_count, last_updated)
                        VALUES (?, ?, ?, ?, 1.0, 1, ?)
                    ''', (pattern_type, pattern_value, material, holder_type, time.time()))
                    
                    cursor.execute('''
                        UPDATE pattern_learning 
                        SET sample_count = sample_count + 1,
                            last_updated = ?
                        WHERE pattern_type = ? AND pattern_value = ? 
                        AND predicted_material = ? AND predicted_type = ?
                    ''', (time.time(), pattern_type, pattern_value, material, holder_type))
                    
            except ValueError:
                pass  # Non-numeric holder ID
                
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update pattern learning: {e}")
            
    def get_learned_prediction(self, holder_id: str) -> Optional[Tuple[str, str, float]]:
        """Get prediction based on learned patterns"""
        try:
            holder_num = int(holder_id)
        except ValueError:
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            patterns = [
                ("id_mod_10", str(holder_num % 10)),
                ("id_mod_15", str(holder_num % 15)),
                ("id_mod_20", str(holder_num % 20)),
                ("id_range_100", str(holder_num // 100)),
                ("id_range_50", str(holder_num // 50))
            ]
            
            best_match = None
            best_confidence = 0.0
            
            for pattern_type, pattern_value in patterns:
                cursor.execute('''
                    SELECT predicted_material, predicted_type, success_rate, sample_count
                    FROM pattern_learning 
                    WHERE pattern_type = ? AND pattern_value = ?
                    ORDER BY sample_count DESC, success_rate DESC
                    LIMIT 1
                ''', (pattern_type, pattern_value))
                
                result = cursor.fetchone()
                if result:
                    material, holder_type, success_rate, sample_count = result
                    # Weight confidence by both success rate and sample size
                    confidence = success_rate * min(sample_count / 10.0, 1.0)
                    
                    if confidence > best_confidence:
                        best_match = (material, holder_type, confidence)
                        best_confidence = confidence
                        
            conn.close()
            return best_match
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get learned prediction: {e}")
            return None
            
    def get_accuracy_stats(self) -> Dict:
        """Get accuracy statistics from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute('SELECT COUNT(*) FROM holder_analysis')
            total_analyzed = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM holder_analysis WHERE verified = TRUE')
            verified_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM accuracy_tracking')
            correction_count = cursor.fetchone()[0]
            
            # Method accuracy
            cursor.execute('''
                SELECT analysis_method, COUNT(*) as count,
                       AVG(confidence) as avg_confidence
                FROM holder_analysis 
                GROUP BY analysis_method
            ''')
            method_stats = cursor.fetchall()
            
            conn.close()
            
            accuracy_rate = ((verified_count - correction_count) / verified_count * 100) if verified_count > 0 else 0
            
            return {
                'total_analyzed': total_analyzed,
                'verified_count': verified_count,
                'correction_count': correction_count,
                'accuracy_rate': accuracy_rate,
                'method_stats': [
                    {
                        'method': row[0],
                        'count': row[1],
                        'avg_confidence': row[2]
                    } for row in method_stats
                ]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get accuracy stats: {e}")
            return {}
            
    def export_for_boss_system(self, format_type: str = "json") -> str:
        """Export data in format compatible with boss's system"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT holder_id, material, holder_type, confidence, 
                       analysis_method, timestamp, verified, photo_hash
                FROM holder_analysis 
                ORDER BY timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            if format_type == "json":
                data = []
                for row in results:
                    data.append({
                        'holder_id': row[0],
                        'material': row[1],
                        'holder_type': row[2],
                        'confidence': row[3],
                        'analysis_method': row[4],
                        'timestamp': row[5],
                        'verified': bool(row[6]),
                        'photo_hash': row[7]
                    })
                
                export_file = f"boss_system_export_{int(time.time())}.json"
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                self.logger.info(f"✅ Exported {len(data)} records to {export_file}")
                return export_file
                
            elif format_type == "csv":
                import csv
                export_file = f"boss_system_export_{int(time.time())}.csv"
                
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['holder_id', 'material', 'holder_type', 'confidence', 
                                   'analysis_method', 'timestamp', 'verified', 'photo_hash'])
                    writer.writerows(results)
                    
                self.logger.info(f"✅ Exported {len(results)} records to {export_file}")
                return export_file
                
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to export data: {e}")
            return ""
            
    def get_photo_hash(self, photo_path: str) -> str:
        """Generate hash for photo file"""
        try:
            with open(photo_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
            
    def bulk_import_existing_data(self, json_file: str) -> bool:
        """Import existing GPT Vision results into local database"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            imported_count = 0
            for item in data:
                analysis = HolderAnalysis(
                    holder_id=item.get('holder_id', ''),
                    material=item.get('material', ''),
                    holder_type=item.get('type', ''),
                    confidence=item.get('confidence', 0.9),
                    analysis_method="imported_gpt_vision",
                    timestamp=time.time(),
                    verified=True  # Assume imported data is verified
                )
                
                if self.store_analysis(analysis):
                    imported_count += 1
                    
            self.logger.info(f"✅ Imported {imported_count} records from {json_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to import data: {e}")
            return False

if __name__ == "__main__":
    # Example usage and testing
    db = LocalAIDatabase()
    
    # Test storing an analysis
    test_analysis = HolderAnalysis(
        holder_id="12345",
        material="kov",
        holder_type="stĺp značky samostatný",
        confidence=0.95,
        analysis_method="local_ai_v2"
    )
    
    db.store_analysis(test_analysis)
    
    # Test retrieval
    retrieved = db.get_analysis("12345")
    if retrieved:
        print(f"✅ Retrieved: {retrieved.material}, {retrieved.holder_type}")
        
    # Test correction
    db.update_with_correction("12345", "betón", "stĺp značky dvojitý")
    
    # Show stats
    stats = db.get_accuracy_stats()
    print(f"📊 Accuracy stats: {stats}")
