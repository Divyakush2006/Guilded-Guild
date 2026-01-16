"""
Movie Name Fixer - Permanently fix inverted article prefixes in movies.csv

This script fixes movie titles like:
  "Shawshank Redemption, The (1994)" → "The Shawshank Redemption (1994)"
  "Dark Knight, The (2008)" → "The Dark Knight (2008)"
  "Godfather, The (1972)" → "The Godfather (1972)"

Usage:
  python fix_movie_names.py --dry-run   # Preview changes without modifying files
  python fix_movie_names.py --apply     # Apply changes and create backup
"""

import pandas as pd
import re
import argparse
from pathlib import Path
from datetime import datetime

# File paths
MOVIES_CSV = Path("movies.csv")
BACKUP_CSV = Path("movies_backup.csv")
REPORT_FILE = Path("movie_name_fixes.txt")


def fix_movie_title(title: str) -> tuple[str, bool]:
    """
    Fix inverted article prefix in movie title.
    
    Args:
        title: Original movie title (e.g., "Shawshank Redemption, The (1994)")
    
    Returns:
        Tuple of (fixed_title, was_changed)
    """
    # Extract year in parentheses if present
    year_match = re.search(r'\((\d{4})\)$', title)
    year_str = f" ({year_match.group(1)})" if year_match else ""
    
    # Remove year for processing
    title_without_year = title.replace(year_str, "").strip()
    
    # Check for inverted articles
    changed = False
    fixed_title = title_without_year
    
    # Handle "Title, The" → "The Title"
    if ', The' in title_without_year:
        fixed_title = 'The ' + title_without_year.replace(', The', '').strip()
        changed = True
    # Handle "Title, A" → "A Title"
    elif ', A' in title_without_year:
        fixed_title = 'A ' + title_without_year.replace(', A', '').strip()
        changed = True
    # Handle "Title, An" → "An Title"
    elif ', An' in title_without_year:
        fixed_title = 'An ' + title_without_year.replace(', An', '').strip()
        changed = True
    
    # Add year back
    final_title = fixed_title + year_str
    
    return final_title, changed


def process_dataset(dry_run: bool = True):
    """
    Process the movies.csv dataset and fix inverted movie names.
    
    Args:
        dry_run: If True, only preview changes. If False, apply changes.
    """
    print("=" * 80)
    print("MOVIE NAME FIXER")
    print("=" * 80)
    print(f"Mode: {'DRY RUN (Preview Only)' if dry_run else 'APPLY CHANGES'}")
    print(f"Dataset: {MOVIES_CSV.absolute()}")
    print()
    
    # Check if file exists
    if not MOVIES_CSV.exists():
        print(f"❌ Error: {MOVIES_CSV} not found!")
        return
    
    # Read dataset
    print("📖 Reading dataset...")
    df = pd.read_csv(MOVIES_CSV)
    total_movies = len(df)
    print(f"   Total movies: {total_movies:,}")
    print()
    
    # Process each movie title
    print("🔍 Analyzing movie titles...")
    changes = []
    fixed_titles = []
    
    for idx, row in df.iterrows():
        original_title = row['title']
        fixed_title, was_changed = fix_movie_title(original_title)
        
        fixed_titles.append(fixed_title)
        
        if was_changed:
            changes.append({
                'movieId': row['movieId'],
                'original': original_title,
                'fixed': fixed_title
            })
    
    # Statistics
    num_changed = len(changes)
    num_unchanged = total_movies - num_changed
    
    print(f"   ✅ Movies to fix: {num_changed:,}")
    print(f"   ⏭️  Unchanged: {num_unchanged:,}")
    print()
    
    # Show sample changes
    if changes:
        print("📝 Sample changes (first 20):")
        print("-" * 80)
        for i, change in enumerate(changes[:20], 1):
            print(f"{i:2d}. {change['original']}")
            print(f"    → {change['fixed']}")
        
        if num_changed > 20:
            print(f"    ... and {num_changed - 20} more changes")
        print()
    
    # Apply changes or save report
    if dry_run:
        print("🔍 DRY RUN MODE - No files modified")
        print()
        print("To apply changes, run:")
        print("  python fix_movie_names.py --apply")
    else:
        # Create backup
        print("💾 Creating backup...")
        df.to_csv(BACKUP_CSV, index=False)
        print(f"   Backup saved: {BACKUP_CSV.absolute()}")
        print()
        
        # Apply fixes
        print("✏️  Applying fixes to dataset...")
        df['title'] = fixed_titles
        df.to_csv(MOVIES_CSV, index=False)
        print(f"   Dataset updated: {MOVIES_CSV.absolute()}")
        print()
        
        # Generate report
        print("📄 Generating report...")
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"Movie Name Fixes Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 80 + "\n\n")
            f.write(f"Total movies: {total_movies:,}\n")
            f.write(f"Movies fixed: {num_changed:,}\n")
            f.write(f"Unchanged: {num_unchanged:,}\n\n")
            f.write(f"Changes:\n")
            f.write(f"-" * 80 + "\n")
            for change in changes:
                f.write(f"ID {change['movieId']}: {change['original']}\n")
                f.write(f"         → {change['fixed']}\n\n")
        
        print(f"   Report saved: {REPORT_FILE.absolute()}")
        print()
        
        print("✅ SUCCESS! Dataset has been fixed.")
        print()
        print("Next steps:")
        print("  1. Verify changes: head movies.csv")
        print("  2. Test TMDB API: python flask_app/test_tmdb_titles.py")
        print("  3. Restart Flask server: python flask_app/app.py")
        print()
        print("To rollback:")
        print(f"  cp {BACKUP_CSV} {MOVIES_CSV}")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Fix inverted article prefixes in movie titles"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files (default)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes and create backup'
    )
    
    args = parser.parse_args()
    
    # Default to dry-run if neither flag is specified
    dry_run = not args.apply
    
    process_dataset(dry_run=dry_run)


if __name__ == "__main__":
    main()
