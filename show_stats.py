#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
import sqlite3

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('n8n_docs.db')
cursor = conn.cursor()

print("\n" + "="*60)
print("📊 Node-Types Statistik nach Kategorie")
print("="*60 + "\n")

cursor.execute('SELECT category, COUNT(*) as count FROM node_types_api GROUP BY category ORDER BY count DESC')
for cat, cnt in cursor.fetchall():
    print(f'   {cat:20s}: {cnt:3d}')

cursor.execute('SELECT COUNT(*) FROM node_types_api')
total = cursor.fetchone()[0]
print(f'\n   {"─"*30}')
print(f'   {"GESAMT":20s}: {total:3d}')
print(f'\n{"="*60}\n')

conn.close()
