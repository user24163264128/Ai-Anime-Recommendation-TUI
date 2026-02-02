# 📊 Data Files Documentation

This document describes the data files used by the AI Anime & Manga Recommendation System.

## 📁 Data Folder Contents

### Raw Data Files

#### `anime_manga_all_anilist.json`
- **Source**: AniList API
- **Format**: JSON array of anime/manga objects
- **Purpose**: Primary data source with detailed metadata
- **Fields**: id, title (romaji/english), description, genres, tags, ratings, popularity, etc.
- **Size**: ~50,000+ entries
- **Update Frequency**: Monthly/quarterly

#### `anime_manga_all_kitsu.json`
- **Source**: Kitsu API
- **Format**: JSON array of anime/manga objects
- **Purpose**: Secondary data source for cross-validation
- **Fields**: Similar to AniList but with different categorization
- **Size**: ~30,000+ entries
- **Update Frequency**: Monthly/quarterly

#### `anime_manga_all_mangadex.json`
- **Source**: MangaDex API
- **Format**: JSON array of manga objects
- **Purpose**: Manga-specific data with chapter information
- **Fields**: Focus on manga with detailed publication info
- **Size**: ~20,000+ entries
- **Update Frequency**: Weekly

### AI/ML Generated Files

#### `embeddings.pkl`
- **Format**: Pickle file containing NumPy arrays
- **Contents**: 384-dimensional sentence embeddings for all titles
- **Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Generation**: Created by `scripts/build_embeddings.py`
- **Size**: ~200-500MB (depends on dataset size)
- **Purpose**: Vector representations for semantic similarity

#### `faiss.index`
- **Format**: FAISS (Facebook AI Similarity Search) index file
- **Algorithm**: HNSW (Hierarchical Navigable Small World)
- **Dimensions**: 384D vectors
- **Purpose**: Fast approximate nearest neighbor search
- **Build Time**: ~5-15 minutes
- **Query Speed**: <10ms per search
- **Size**: ~100-300MB

## 🔄 Data Pipeline

### 1. Data Collection
```bash
# Fetch from APIs
python data_get.py
python fetch_data.py
```

### 2. Data Import
```bash
# Load into MongoDB
python json_to_database.py
```

### 3. AI Processing
```bash
# Generate embeddings
python scripts/build_embeddings.py

# Build search index
python scripts/build_index.py
```

## 📈 Data Statistics

| Dataset | Entries | Primary Use | Last Updated |
|---------|---------|-------------|--------------|
| AniList | ~150k | Anime/Manga | Monthly |
| Kitsu | ~100k | Anime/Manga | Monthly |
| MangaDex | ~100k | Manga | Weekly |
| **Total** | **~350k** | **All** | **Varies** |

## 🗂️ Data Schema

### Common Fields
- `id`: Unique identifier
- `title_romaji`: Japanese title
- `title_english`: English title
- `description`: Plot summary
- `genres`: Array of genre strings
- `tags`: Array of descriptive tags
- `type`: "ANIME" or "MANGA"
- `average_score`: Rating (0-100)
- `popularity`: View count/popularity score
- `status`: "FINISHED", "ONGOING", etc.

### Anime-Specific Fields
- `episodes`: Number of episodes
- `duration`: Episode length in minutes
- `season`: Release season
- `studios`: Production studios

### Manga-Specific Fields
- `chapters`: Number of chapters
- `volumes`: Number of volumes
- `authors`: Creator information

## ⚠️ Important Notes

### File Management
- **Raw JSON files**: Can be regenerated from APIs
- **Embeddings & Index**: Take significant time to rebuild
- **Backup Strategy**: Keep embeddings/index in version control if small, otherwise regenerate

### Storage Considerations
- **Embeddings**: ~200MB for 100k titles
- **FAISS Index**: ~100MB for 100k titles
- **MongoDB**: ~500MB for full dataset
- **Total**: ~800MB+ for complete system

### Update Process
1. Fetch new data from APIs
2. Update MongoDB collection
3. Regenerate embeddings (if schema changes)
4. Rebuild FAISS index
5. Test recommendation quality

## 🔍 Data Quality

### Validation Checks
- Title uniqueness across sources
- Genre normalization
- Rating scale consistency
- Missing data handling
- Duplicate detection

### Data Sources Reliability
- **AniList**: High quality, comprehensive metadata
- **Kitsu**: Good coverage, different categorization
- **MangaDex**: Excellent manga data, frequent updates

## 📋 Maintenance

### Regular Tasks
- **Weekly**: Update MangaDex data
- **Monthly**: Refresh AniList/Kitsu data
- **Quarterly**: Full data pipeline rebuild
- **As needed**: Rebuild embeddings after model updates

### Monitoring
- Check data file sizes for growth
- Monitor API rate limits
- Validate recommendation quality
- Update dependencies as needed
