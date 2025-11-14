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
print("GitHub Node-Types (erste 20) - Groß-/Kleinschreibung")
print("="*80 + "\n")

cursor.execute('SELECT node_type, display_name FROM node_types_github ORDER BY node_type LIMIT 20')
for nt, dn in cursor.fetchall():
    print(f'{nt:45s} | {dn}')

print("\n" + "="*80)
print("API/Dokumentation Node-Types (erste 20) - Groß-/Kleinschreibung")
print("="*80 + "\n")

cursor.execute("SELECT node_type, display_name FROM node_types_api WHERE category='App' ORDER BY node_type LIMIT 20")
for nt, dn in cursor.fetchall():
    print(f'{nt:45s} | {dn}')

print("\n" + "="*80)
print("Vergleich: Gleiche Nodes aus beiden Quellen")
print("="*80 + "\n")

# Finde Nodes die in beiden Tabellen sind
cursor.execute("""
    SELECT
        g.node_type as github_type,
        a.node_type as api_type,
        g.display_name as github_name,
        a.display_name as api_name
    FROM node_types_github g
    INNER JOIN node_types_api a ON LOWER(g.node_type) = LOWER(a.node_type)
    WHERE g.node_type != a.node_type
    LIMIT 20
""")

print("GitHub Type                               | API Type")
print("-" * 80)
for g_type, a_type, g_name, a_name in cursor.fetchall():
    print(f'{g_type:45s} | {a_type}')

conn.close()
