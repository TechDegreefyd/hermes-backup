import re

with open('/workspace/build_master_fixed.py', 'r') as f:
    content = f.read()

old_chart = """        m = f.groupby('Date_Parsed').agg({'Spends':'sum', 'Pannel_Lead':'sum', 'Lead_LMS':'sum'}).reset_index().sort_values('Date_Parsed')
        m['CPL_P'] = m['Spends'] / m['Pannel_Lead']; m['CPL_L'] = m['Spends'] / m['Lead_LMS']; m['X'] = m['Date_Parsed'].dt.strftime('%b %d')
        m = m.replace([np.inf, -np.inf], 0).fillna(0)
        def chart(y1, y2, l1, l2, t, isc):
            plt.rcParams.update({"axes.facecolor":"#ffffff","figure.facecolor":"#ffffff","text.color":"#0f172a","font.family":"sans-serif"})
            fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
            ax.plot(m['X'], m[y1], marker='o', color='#059669' if not isc else '#d97706', label=l1, linewidth=2)
            ax.plot(m['X'], m[y2], marker='s', color='#7c3aed' if not isc else '#dc2626', label=l2, linewidth=2)
            for i,v in enumerate(m[y1]): ax.text(i,v,(f"₹{v:,.0f}" if isc else f"{v:,.0f}"),ha='center',va='bottom',fontweight='bold',fontsize=8)
            for i,v in enumerate(m[y2]): ax.text(i,v,(f"₹{v:,.0f}" if isc else f"{v:,.0f}"),ha='center',va='top',fontweight='bold',fontsize=8)
            ax.set_title(t, fontweight='bold'); fig.tight_layout(); buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)"""

new_chart = """        m = f.groupby('Date_Parsed').agg({'Spends':'sum', 'Pannel_Lead':'sum', 'Lead_LMS':'sum'}).reset_index().sort_values('Date_Parsed')
        # Only show last 20 days so graphs are clean and readable
        m = m.tail(20).reset_index(drop=True)
        m['CPL_P'] = m['Spends'] / m['Pannel_Lead']; m['CPL_L'] = m['Spends'] / m['Lead_LMS']; m['X'] = m['Date_Parsed'].dt.strftime('%d %b')
        m = m.replace([np.inf, -np.inf], 0).fillna(0)
        def chart(y1, y2, l1, l2, t, isc):
            plt.rcParams.update({"axes.facecolor":"#ffffff","figure.facecolor":"#ffffff","text.color":"#0f172a","font.family":"sans-serif"})
            fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
            ax.plot(m['X'], m[y1], marker='o', color='#059669' if not isc else '#d97706', label=l1, linewidth=2)
            ax.plot(m['X'], m[y2], marker='s', color='#7c3aed' if not isc else '#dc2626', label=l2, linewidth=2)
            ax.legend(loc='upper left', bbox_to_anchor=(0, 1.15), ncol=2, frameon=False)
            ax.grid(axis='y', linestyle='--', alpha=0.4)
            plt.xticks(rotation=45, ha='right')
            for i,v in enumerate(m[y1]): 
                if v > 0: ax.text(i, v + (v*0.02), (f"₹{v:,.0f}" if isc else f"{v:,.0f}"), ha='center', va='bottom', fontweight='bold', fontsize=9, color='#059669' if not isc else '#d97706')
            for i,v in enumerate(m[y2]): 
                if v > 0: ax.text(i, v - (v*0.02), (f"₹{v:,.0f}" if isc else f"{v:,.0f}"), ha='center', va='top', fontweight='bold', fontsize=9, color='#7c3aed' if not isc else '#dc2626')
            
            # Pad the y-axis a bit so text doesn't get cut off
            y_max = max(m[y1].max(), m[y2].max())
            ax.set_ylim(bottom=0, top=y_max * 1.15 if y_max > 0 else 100)
            
            ax.set_title(t + " (Last 20 Days)", fontweight='bold', pad=20)
            fig.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            plt.close(fig)"""

content = content.replace(old_chart, new_chart)

caption_old = r"✅ **Date Glitch FIXED:** MTD now accurately captures action events.\n✅ **Attribution FIXED:** FFH matches Form Date, Admissions/Inv match Admission Date. You will now see the exact values from your manual list for May 1-4!"
caption_new = r"✅ **Graphs FIXED AND CLARIFIED:** Trends now show a clean 20-day window. X-axis rotated, grids added, text overlapping removed, and dynamically scaled to prevent cutoff!\n✅ **Attribution FIXED:** FFH mapped to Form Date, Admissions/Inv to Admission Date."

content = content.replace(caption_old, caption_new)

with open('/workspace/build_master_fixed.py', 'w') as f:
    f.write(content)

