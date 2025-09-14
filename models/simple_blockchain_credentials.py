"""
Simplified Blockchain Credential Verification System
Provides tamper-proof credential storage and instant verification without external dependencies
"""

import hashlib
import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SimpleBlockchainCredentialVerifier:
    """
    Simplified blockchain-inspired credential verification system
    Features:
    - Tamper-proof credential storage using SHA-256 hashing
    - Instant verification of degrees/certifications
    - Work experience validation
    - Fraud prevention system
    - No external dependencies required
    """
    
    def __init__(self, db_path: str = "credentials_blockchain.db"):
        self.db_path = db_path
        self.init_blockchain_db()
        logger.info("Simple Blockchain Credential Verifier initialized")
    
    def init_blockchain_db(self):
        """Initialize the blockchain credential database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Credential blocks table (blockchain structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credential_blocks (
                block_id INTEGER PRIMARY KEY AUTOINCREMENT,
                previous_hash TEXT NOT NULL,
                timestamp REAL NOT NULL,
                credential_data TEXT NOT NULL,
                block_hash TEXT NOT NULL UNIQUE,
                merkle_root TEXT NOT NULL,
                nonce INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Verified institutions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verified_institutions (
                institution_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL, -- university, certification_body, company
                verification_status TEXT DEFAULT 'verified',
                country TEXT,
                accreditation_body TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Fraud detection logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fraud_detection_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT NOT NULL,
                credential_hash TEXT NOT NULL,
                fraud_type TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                detection_method TEXT NOT NULL,
                details TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize with genesis block if empty
        self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the genesis block if blockchain is empty"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM credential_blocks")
        if cursor.fetchone()[0] == 0:
            genesis_data = {
                "type": "genesis",
                "message": "Telus AI Talent Platform Credential Blockchain Genesis Block",
                "timestamp": time.time()
            }
            
            genesis_hash = self._calculate_hash("0", json.dumps(genesis_data), 0)
            
            cursor.execute('''
                INSERT INTO credential_blocks 
                (previous_hash, timestamp, credential_data, block_hash, merkle_root, nonce)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("0", time.time(), json.dumps(genesis_data), genesis_hash, genesis_hash, 0))
            
            conn.commit()
        
        conn.close()
    
    def _calculate_hash(self, previous_hash: str, data: str, nonce: int) -> str:
        """Calculate SHA-256 hash for a block"""
        block_string = f"{previous_hash}{data}{nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def add_credential_to_blockchain(self, credential_data: Dict) -> str:
        """
        Add a new credential to the blockchain
        
        Args:
            credential_data: Dictionary containing credential information
            
        Returns:
            Block hash of the new credential block
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the last block hash
        cursor.execute("SELECT block_hash FROM credential_blocks ORDER BY block_id DESC LIMIT 1")
        last_block = cursor.fetchone()
        previous_hash = last_block[0] if last_block else "0"
        
        # Add timestamp and unique ID
        credential_data['timestamp'] = time.time()
        credential_data['credential_id'] = hashlib.sha256(
            f"{credential_data.get('candidate_id', '')}{credential_data['timestamp']}".encode()
        ).hexdigest()[:16]
        
        # Calculate merkle root (simplified for single transaction)
        data_string = json.dumps(credential_data, sort_keys=True)
        merkle_root = hashlib.sha256(data_string.encode()).hexdigest()
        
        # Mine the block (simplified proof of work)
        nonce = 0
        while True:
            block_hash = self._calculate_hash(previous_hash, data_string, nonce)
            if block_hash.startswith("000"):  # Reduced difficulty for demo
                break
            nonce += 1
            if nonce > 100000:  # Prevent infinite loop
                break
        
        # Store in blockchain
        cursor.execute('''
            INSERT INTO credential_blocks 
            (previous_hash, timestamp, credential_data, block_hash, merkle_root, nonce)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (previous_hash, time.time(), data_string, block_hash, merkle_root, nonce))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Credential added to blockchain: {block_hash}")
        return block_hash
    
    def verify_credential(self, credential_hash: str) -> Dict:
        """
        Verify a credential using its blockchain hash
        
        Args:
            credential_hash: Hash of the credential block
            
        Returns:
            Verification result with status and details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find the credential block
        cursor.execute('''
            SELECT credential_data, previous_hash, nonce, timestamp
            FROM credential_blocks 
            WHERE block_hash = ?
        ''', (credential_hash,))
        
        block_data = cursor.fetchone()
        if not block_data:
            return {
                "status": "not_found",
                "verified": False,
                "message": "Credential not found in blockchain"
            }
        
        credential_data, previous_hash, nonce, timestamp = block_data
        
        # Verify block hash
        calculated_hash = self._calculate_hash(previous_hash, credential_data, nonce)
        if calculated_hash != credential_hash:
            return {
                "status": "tampered",
                "verified": False,
                "message": "Credential has been tampered with"
            }
        
        # Parse credential data
        try:
            credential_info = json.loads(credential_data)
        except json.JSONDecodeError:
            return {
                "status": "corrupted",
                "verified": False,
                "message": "Credential data is corrupted"
            }
        
        # Additional verification checks
        verification_score = self._calculate_verification_score(credential_info)
        
        conn.close()
        
        return {
            "status": "verified",
            "verified": True,
            "credential_data": credential_info,
            "verification_score": verification_score,
            "blockchain_timestamp": timestamp,
            "message": "Credential successfully verified"
        }
    
    def _calculate_verification_score(self, credential_data: Dict) -> float:
        """Calculate verification confidence score"""
        score = 0.0
        
        # Base score for being in blockchain
        score += 50.0
        
        # Institution verification
        if self._is_institution_verified(credential_data.get('institution_id')):
            score += 30.0
        
        # Credential type scoring
        credential_type = credential_data.get('type', '').lower()
        if credential_type in ['degree', 'certification', 'license']:
            score += 20.0
        elif credential_type in ['work_experience', 'skill_assessment']:
            score += 15.0
        
        return min(score, 100.0)
    
    def _is_institution_verified(self, institution_id: str) -> bool:
        """Check if institution is verified"""
        if not institution_id:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT verification_status FROM verified_institutions 
            WHERE institution_id = ?
        ''', (institution_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result and result[0] == 'verified'
    
    def add_verified_institution(self, institution_data: Dict) -> bool:
        """Add a verified institution to the system"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO verified_institutions 
                (institution_id, name, type, country, accreditation_body)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                institution_data['institution_id'],
                institution_data['name'],
                institution_data['type'],
                institution_data.get('country', ''),
                institution_data.get('accreditation_body', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def detect_credential_fraud(self, candidate_id: str, submitted_credentials: List[Dict]) -> Dict:
        """
        Detect potential credential fraud using various methods
        
        Args:
            candidate_id: ID of the candidate
            submitted_credentials: List of credentials to verify
            
        Returns:
            Fraud detection results
        """
        fraud_indicators = []
        overall_risk_score = 0.0
        
        for credential in submitted_credentials:
            # Check for duplicate credentials
            if self._check_duplicate_credentials(credential):
                fraud_indicators.append({
                    "type": "duplicate_credential",
                    "severity": "high",
                    "description": "Identical credential found for different candidate"
                })
                overall_risk_score += 30.0
            
            # Check institution validity
            institution_id = credential.get('institution_id')
            if institution_id and not self._is_institution_verified(institution_id):
                fraud_indicators.append({
                    "type": "invalid_institution",
                    "severity": "high",
                    "description": "Institution not found in verified database"
                })
                overall_risk_score += 25.0
            
            # Check format and structure
            if not self._validate_credential_format(credential):
                fraud_indicators.append({
                    "type": "format_anomaly",
                    "severity": "low",
                    "description": "Credential format appears suspicious"
                })
                overall_risk_score += 10.0
        
        # Log fraud detection results
        if fraud_indicators:
            self._log_fraud_detection(candidate_id, fraud_indicators, overall_risk_score)
        
        return {
            "candidate_id": candidate_id,
            "risk_score": min(overall_risk_score, 100.0),
            "risk_level": self._get_risk_level(overall_risk_score),
            "fraud_indicators": fraud_indicators,
            "recommendation": self._get_fraud_recommendation(overall_risk_score)
        }
    
    def _check_duplicate_credentials(self, credential: Dict) -> bool:
        """Check for duplicate credentials across candidates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create a hash of the credential content (excluding candidate_id)
        credential_copy = credential.copy()
        credential_copy.pop('candidate_id', None)
        credential_copy.pop('timestamp', None)
        content_hash = hashlib.sha256(json.dumps(credential_copy, sort_keys=True).encode()).hexdigest()
        
        cursor.execute('''
            SELECT COUNT(*) FROM credential_blocks 
            WHERE credential_data LIKE ?
        ''', (f'%{content_hash}%',))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 1
    
    def _validate_credential_format(self, credential: Dict) -> bool:
        """Validate credential format and required fields"""
        required_fields = ['type', 'title']
        
        for field in required_fields:
            if field not in credential or not credential[field]:
                return False
        
        # Check for suspicious patterns
        title = credential.get('title', '').lower()
        suspicious_patterns = ['fake', 'test', 'sample', 'dummy']
        
        for pattern in suspicious_patterns:
            if pattern in title:
                return False
        
        return True
    
    def _log_fraud_detection(self, candidate_id: str, fraud_indicators: List[Dict], risk_score: float):
        """Log fraud detection results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for indicator in fraud_indicators:
            cursor.execute('''
                INSERT INTO fraud_detection_logs 
                (candidate_id, credential_hash, fraud_type, confidence_score, detection_method, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                candidate_id,
                hashlib.sha256(f"{candidate_id}{time.time()}".encode()).hexdigest()[:16],
                indicator['type'],
                risk_score,
                'automated_detection',
                json.dumps(indicator)
            ))
        
        conn.commit()
        conn.close()
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_fraud_recommendation(self, risk_score: float) -> str:
        """Get recommendation based on risk score"""
        if risk_score >= 70:
            return "REJECT - High fraud risk detected. Manual investigation required."
        elif risk_score >= 40:
            return "REVIEW - Medium fraud risk. Additional verification recommended."
        elif risk_score >= 20:
            return "CAUTION - Low fraud risk. Monitor for additional indicators."
        else:
            return "PROCEED - Minimal fraud risk detected."
    
    def get_candidate_credential_summary(self, candidate_id: str) -> Dict:
        """Get comprehensive credential summary for a candidate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all credentials for candidate
        cursor.execute('''
            SELECT credential_data, block_hash, timestamp 
            FROM credential_blocks 
            WHERE credential_data LIKE ?
            ORDER BY timestamp DESC
        ''', (f'%"candidate_id": "{candidate_id}"%',))
        
        credentials = []
        total_verification_score = 0.0
        
        for row in cursor.fetchall():
            try:
                credential_data = json.loads(row[0])
                if credential_data.get('candidate_id') == candidate_id:
                    verification_result = self.verify_credential(row[1])
                    credentials.append({
                        "credential_data": credential_data,
                        "block_hash": row[1],
                        "verification_result": verification_result,
                        "blockchain_timestamp": row[2]
                    })
                    total_verification_score += verification_result.get('verification_score', 0)
            except json.JSONDecodeError:
                continue
        
        # Calculate fraud risk
        fraud_analysis = self.detect_credential_fraud(
            candidate_id, 
            [cred['credential_data'] for cred in credentials]
        )
        
        conn.close()
        
        return {
            "candidate_id": candidate_id,
            "total_credentials": len(credentials),
            "average_verification_score": total_verification_score / len(credentials) if credentials else 0,
            "credentials": credentials,
            "fraud_analysis": fraud_analysis,
            "overall_trust_score": self._calculate_overall_trust_score(credentials, fraud_analysis),
            "summary_generated_at": datetime.now().isoformat()
        }
    
    def _calculate_overall_trust_score(self, credentials: List[Dict], fraud_analysis: Dict) -> float:
        """Calculate overall trust score for candidate"""
        if not credentials:
            return 0.0
        
        # Base score from verification scores
        avg_verification = sum(
            cred['verification_result'].get('verification_score', 0) 
            for cred in credentials
        ) / len(credentials)
        
        # Penalty for fraud risk
        fraud_penalty = fraud_analysis.get('risk_score', 0) * 0.5
        
        # Bonus for multiple verified credentials
        credential_bonus = min(len(credentials) * 5, 20)
        
        trust_score = avg_verification + credential_bonus - fraud_penalty
        return max(0.0, min(100.0, trust_score))

# Initialize blockchain credential verifier
blockchain_verifier = SimpleBlockchainCredentialVerifier()
