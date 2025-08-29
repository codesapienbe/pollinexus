"""
DuckDB service for efficient data operations in Pollinexus.

This service leverages DuckDB's capabilities for direct CSV access,
vector operations, and analytical queries.
"""

import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DuckDBService:
    """Service for DuckDB operations with direct CSV access and vector calculations."""
    
    def __init__(self, db_path: str = "pollinexus.db"):
        """Initialize DuckDB service."""
        self.db_path = db_path
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish connection to DuckDB."""
        try:
            self.connection = duckdb.connect(self.db_path)
            # Enable extensions for additional functionality
            self.connection.execute("INSTALL httpfs")
            self.connection.execute("LOAD httpfs")
            logger.info(f"Connected to DuckDB database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("DuckDB connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def load_csv_direct(self, csv_path: str, table_name: str = None) -> str:
        """
        Load CSV file directly into DuckDB without pandas.
        
        Args:
            csv_path: Path to the CSV file
            table_name: Name for the table (defaults to filename without extension)
            
        Returns:
            str: Canonical view name used
        """
        if table_name is None:
            table_name = Path(csv_path).stem
        
        try:
            # Create raw table from CSV with automatic schema inference
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name}_raw AS 
            SELECT * FROM read_csv_auto('{csv_path}')
            """
            self.connection.execute(create_table_query)
            
            # Create a canonical view with aliased columns expected by analysis
            canonical_view = f"{table_name}_canonical"
            self.connection.execute(f"DROP VIEW IF EXISTS {canonical_view}")
            alias_query = f"""
            CREATE VIEW {canonical_view} AS
            SELECT 
                COALESCE("plant species", plant_species) AS plant_species,
                COALESCE("Species", bee_species) AS bee_species,
                COALESCE(season, season) AS season,
                COALESCE(site, site) AS site,
                COALESCE(plot, native_or_non) AS native_or_non,
                COALESCE(sampling, sampling) AS sampling,
                COALESCE(date, date) AS date,
                COALESCE("start time", start_time) AS start_time,
                COALESCE("end time", end_time) AS end_time,
                COALESCE("Sex", sex) AS sex,
                COALESCE(parasitic, parasitic) AS parasitic,
                COALESCE(nesting, nesting) AS nesting,
                COALESCE("non-native bee", nonnative_bee) AS nonnative_bee,
                COALESCE("no of specimens in sample", bees_num) AS bees_num,
                *
            FROM {table_name}_raw
            """
            self.connection.execute(alias_query)
            
            # Get row count from view
            count = self.connection.execute(f"SELECT COUNT(*) FROM {canonical_view}").fetchone()[0]
            logger.info(f"Loaded {count} rows from {csv_path} into view {canonical_view}")
            
            return canonical_view
            
        except Exception as e:
            logger.error(f"Error loading CSV {csv_path}: {e}")
            raise
    
    def query_to_dataframe(self, query: str) -> pd.DataFrame:
        """
        Execute query and return results as pandas DataFrame.
        
        Args:
            query: SQL query to execute
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            return self.connection.execute(query).df()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def get_dataset_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a dataset table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dict containing dataset information
        """
        try:
            # Get basic table info
            info_query = f"""
            DESCRIBE {table_name}
            """
            schema_info = self.query_to_dataframe(info_query)
            
            # Get row count
            count_query = f"SELECT COUNT(*) as total_rows FROM {table_name}"
            row_count = self.connection.execute(count_query).fetchone()[0]
            
            # Get column statistics
            stats = {}
            for _, row in schema_info.iterrows():
                col_name = row['column_name']
                col_type = row['column_type']
                
                # Get unique values count for categorical columns
                if 'VARCHAR' in col_type.upper() or 'CHAR' in col_type.upper():
                    unique_query = f"SELECT COUNT(DISTINCT {col_name}) as unique_count FROM {table_name}"
                    unique_count = self.connection.execute(unique_query).fetchone()[0]
                    stats[col_name] = {
                        'type': col_type,
                        'unique_count': unique_count
                    }
                else:
                    # For numeric columns, get basic stats
                    try:
                        stats_query = f"""
                        SELECT 
                            MIN({col_name}) as min_val,
                            MAX({col_name}) as max_val,
                            AVG({col_name}) as avg_val,
                            COUNT({col_name}) as non_null_count
                        FROM {table_name}
                        """
                        col_stats = self.connection.execute(stats_query).fetchone()
                        stats[col_name] = {
                            'type': col_type,
                            'min': col_stats[0],
                            'max': col_stats[1],
                            'avg': col_stats[2],
                            'non_null_count': col_stats[3]
                        }
                    except:
                        stats[col_name] = {'type': col_type}
            
            return {
                'table_name': table_name,
                'total_rows': row_count,
                'columns': schema_info.to_dict('records'),
                'column_stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting dataset info for {table_name}: {e}")
            raise
    
    def analyze_bee_preferences(self, table_name: str) -> Dict[str, Any]:
        """
        Analyze bee preferences using DuckDB's analytical capabilities.
        
        Args:
            table_name: Name of the dataset table
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Analyze bee species distribution
            bee_analysis_query = f"""
            SELECT 
                bee_species,
                COUNT(*) as observation_count,
                AVG(bees_num) as avg_bees_per_observation,
                SUM(bees_num) as total_bees,
                AVG(CASE WHEN nonnative_bee = 0 THEN 1.0 ELSE 0.0 END) as native_bee_ratio
            FROM {table_name}
            WHERE bee_species IS NOT NULL
            GROUP BY bee_species
            ORDER BY total_bees DESC
            """
            bee_analysis = self.query_to_dataframe(bee_analysis_query)
            
            # Analyze plant preferences
            plant_analysis_query = f"""
            SELECT 
                plant_species,
                COUNT(*) as observation_count,
                AVG(bees_num) as avg_bees_per_observation,
                SUM(bees_num) as total_bees,
                AVG(CASE WHEN nonnative_bee = 0 THEN 1.0 ELSE 0.0 END) as native_bee_ratio
            FROM {table_name}
            WHERE plant_species IS NOT NULL AND plant_species != 'None'
            GROUP BY plant_species
            ORDER BY total_bees DESC
            """
            plant_analysis = self.query_to_dataframe(plant_analysis_query)
            
            # Seasonal analysis
            seasonal_analysis_query = f"""
            SELECT 
                season,
                COUNT(*) as observation_count,
                AVG(bees_num) as avg_bees_per_observation,
                SUM(bees_num) as total_bees
            FROM {table_name}
            WHERE season IS NOT NULL
            GROUP BY season
            ORDER BY total_bees DESC
            """
            seasonal_analysis = self.query_to_dataframe(seasonal_analysis_query)
            
            # Site comparison
            site_analysis_query = f"""
            SELECT 
                site,
                COUNT(*) as observation_count,
                AVG(bees_num) as avg_bees_per_observation,
                SUM(bees_num) as total_bees,
                COUNT(DISTINCT bee_species) as unique_bee_species,
                COUNT(DISTINCT plant_species) as unique_plant_species
            FROM {table_name}
            WHERE site IS NOT NULL
            GROUP BY site
            ORDER BY total_bees DESC
            """
            site_analysis = self.query_to_dataframe(site_analysis_query)
            
            return {
                'bee_species_analysis': bee_analysis.to_dict('records'),
                'plant_species_analysis': plant_analysis.to_dict('records'),
                'seasonal_analysis': seasonal_analysis.to_dict('records'),
                'site_analysis': site_analysis.to_dict('records'),
                'summary': {
                    'total_observations': bee_analysis['observation_count'].sum(),
                    'total_bees': bee_analysis['total_bees'].sum(),
                    'unique_bee_species': len(bee_analysis),
                    'unique_plant_species': len(plant_analysis)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing bee preferences: {e}")
            raise
    
    def get_plant_recommendations(self, table_name: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Generate plant recommendations based on bee preferences.
        
        Args:
            table_name: Name of the dataset table
            top_n: Number of top recommendations to return
            
        Returns:
            List of plant recommendations
        """
        try:
            # Calculate recommendation scores
            recommendation_query = f"""
            SELECT 
                plant_species,
                COUNT(*) as observation_count,
                AVG(bees_num) as avg_bees_per_observation,
                SUM(bees_num) as total_bees,
                AVG(CASE WHEN nonnative_bee = 0 THEN 1.0 ELSE 0.0 END) as native_bee_ratio,
                -- Calculate recommendation score
                (COUNT(*) * 0.4 + AVG(bees_num) * 0.3 + AVG(CASE WHEN nonnative_bee = 0 THEN 1.0 ELSE 0.0 END) * 0.3) as recommendation_score
            FROM {table_name}
            WHERE plant_species IS NOT NULL AND plant_species != 'None'
            GROUP BY plant_species
            ORDER BY recommendation_score DESC
            LIMIT {top_n}
            """
            
            recommendations = self.query_to_dataframe(recommendation_query)
            
            # Format results
            result = []
            for i, row in recommendations.iterrows():
                result.append({
                    'rank': i + 1,
                    'plant_species': row['plant_species'],
                    'score': float(row['recommendation_score']),
                    'observation_count': int(row['observation_count']),
                    'avg_bees_per_observation': float(row['avg_bees_per_observation']),
                    'total_bees': int(row['total_bees']),
                    'native_bee_ratio': float(row['native_bee_ratio']),
                    'reasoning': f"High bee abundance ({row['total_bees']} total bees) with {row['native_bee_ratio']:.1%} native bee ratio"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating plant recommendations: {e}")
            raise
    
    def export_results(self, query: str, output_path: str, format: str = 'csv'):
        """
        Export query results to file.
        
        Args:
            query: SQL query to execute
            output_path: Path for output file
            format: Output format ('csv', 'parquet', 'json')
        """
        try:
            if format.lower() == 'csv':
                self.connection.execute(f"COPY ({query}) TO '{output_path}' (HEADER, DELIMITER ',')")
            elif format.lower() == 'parquet':
                self.connection.execute(f"COPY ({query}) TO '{output_path}' (FORMAT PARQUET)")
            elif format.lower() == 'json':
                self.connection.execute(f"COPY ({query}) TO '{output_path}' (FORMAT JSON)")
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Exported results to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            raise 