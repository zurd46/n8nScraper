#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
import sqlite3

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('n8n_docs.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("📊 Community Nodes Status")
print("="*80 + "\n")

# Count community nodes
cursor.execute("SELECT COUNT(*) FROM community_nodes")
count = cursor.fetchone()[0]
print(f"✓ Community Nodes in Datenbank: {count:,}")

if count > 0:
    print("\n" + "-"*80)
    print("📦 Beispiele (erste 10):")
    print("-"*80 + "\n")

    cursor.execute("""
        SELECT package_name, description
        FROM community_nodes
        LIMIT 10
    """)

    for pkg_name, desc in cursor.fetchall():
        desc_short = (desc[:60] + '...') if desc and len(desc) > 60 else desc or ''
        print(f"• {pkg_name}")
        if desc_short:
            print(f"  {desc_short}")
        print()

print("="*80)
print("📍 Speicherort: n8n_docs.db -> Tabelle 'community_nodes'")
print("="*80 + "\n")

conn.close()
