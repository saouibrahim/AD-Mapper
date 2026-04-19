from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from typing import List, Dict, Any
import os
import uuid

SEVERITY_COLORS = {
    "critique": colors.HexColor("#dc2626"),
    "haute": colors.HexColor("#ea580c"),
    "moyenne": colors.HexColor("#d97706"),
    "basse": colors.HexColor("#65a30d"),
    "info": colors.HexColor("#2563eb"),
}

RED_DARK = colors.HexColor("#1a0a0a")
RED_MID = colors.HexColor("#7f1d1d")
RED_ACCENT = colors.HexColor("#ef4444")
GREY_BG = colors.HexColor("#f8f8f8")
WHITE = colors.white
BLACK = colors.HexColor("#111111")


class ReportService:
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate(
        self,
        title: str,
        mission: str,
        operator: str,
        stats: Dict[str, Any],
        misconfigs: List[Dict[str, Any]],
        attack_paths: List[Dict[str, Any]],
    ) -> str:
        filename = f"rapport_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # ── Cover ──────────────────────────────────────────────────────────
        story.append(Spacer(1, 3 * cm))
        story.append(Paragraph(
            '<font color="#ef4444">⬛</font> RED TEAM REPORT',
            ParagraphStyle("cover_tag", fontSize=10, textColor=RED_ACCENT, spaceAfter=6),
        ))
        story.append(Paragraph(
            title,
            ParagraphStyle("cover_title", fontSize=28, textColor=BLACK, fontName="Helvetica-Bold", spaceAfter=12, leading=34),
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=RED_ACCENT))
        story.append(Spacer(1, 0.5 * cm))

        meta = [
            ["Mission", mission or "—"],
            ["Opérateur", operator or "—"],
            ["Date", datetime.now().strftime("%d/%m/%Y")],
            ["Classification", "CONFIDENTIEL"],
        ]
        t = Table(meta, colWidths=[4 * cm, 12 * cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), RED_MID),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [GREY_BG, WHITE]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5e5")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(PageBreak())

        # ── Executive Summary ──────────────────────────────────────────────
        story.append(self._h1("Résumé Exécutif"))
        story.append(Paragraph(
            f"Cette évaluation Red Team a analysé le domaine Active Directory. "
            f"L'énumération a identifié <b>{stats.get('users', 0)} utilisateurs</b>, "
            f"<b>{stats.get('computers', 0)} machines</b> et <b>{stats.get('groups', 0)} groupes</b>. "
            f"Un total de <b>{len(misconfigs)} mauvaises configurations</b> ont été détectées, "
            f"dont {sum(1 for m in misconfigs if m.get('severity') in ('critique', 'haute'))} à risque élevé ou critique.",
            styles["Normal"],
        ))
        story.append(Spacer(1, 0.4 * cm))

        # Stats table
        sev_counts = {"critique": 0, "haute": 0, "moyenne": 0, "basse": 0}
        for m in misconfigs:
            s = m.get("severity", "basse")
            if s in sev_counts:
                sev_counts[s] += 1

        stat_data = [
            ["Utilisateurs", "Machines", "Groupes", "Admins", "Kerberoastables"],
            [
                str(stats.get("users", 0)),
                str(stats.get("computers", 0)),
                str(stats.get("groups", 0)),
                str(stats.get("admin_users", 0)),
                str(stats.get("kerberoastable", 0)),
            ],
        ]
        st = Table(stat_data, colWidths=[3.2 * cm] * 5)
        st.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), RED_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, 1), GREY_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5e5")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(st)
        story.append(Spacer(1, 0.8 * cm))

        # ── Misconfigurations ──────────────────────────────────────────────
        story.append(self._h1("Mauvaises Configurations Détectées"))

        for idx, mc in enumerate(misconfigs, 1):
            sev = mc.get("severity", "info")
            sev_color = SEVERITY_COLORS.get(sev, colors.grey)

            story.append(Paragraph(
                f'<font color="#{sev_color.hexval()[2:] if hasattr(sev_color, "hexval") else "888888"}">▐</font> '
                f'<b>[{sev.upper()}]</b> {mc.get("title", "?")}',
                ParagraphStyle(f"mc_title_{idx}", fontSize=11, fontName="Helvetica-Bold",
                               textColor=BLACK, spaceAfter=4, spaceBefore=10),
            ))
            story.append(Paragraph(mc.get("description", ""), styles["Normal"]))

            if mc.get("affected_objects"):
                affected_str = ", ".join(mc["affected_objects"][:10])
                if len(mc["affected_objects"]) > 10:
                    affected_str += f" (+{len(mc['affected_objects']) - 10} autres)"
                story.append(Paragraph(f"<b>Objets affectés :</b> {affected_str}",
                                       ParagraphStyle("aff", fontSize=9, textColor=colors.HexColor("#555555"), spaceAfter=2)))

            story.append(Paragraph(f"<b>Recommandation :</b> {mc.get('recommendation', '')}",
                                   ParagraphStyle("rec", fontSize=9, textColor=RED_MID, spaceAfter=6)))

            if mc.get("cvss_score"):
                story.append(Paragraph(f"<b>CVSS :</b> {mc['cvss_score']}/10",
                                       ParagraphStyle("cvss", fontSize=9)))

            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e5e5")))

        story.append(PageBreak())

        # ── Attack Paths ───────────────────────────────────────────────────
        story.append(self._h1("Chemins d'Attaque Identifiés"))

        for idx, path in enumerate(attack_paths, 1):
            sev = path.get("severity", "info")
            story.append(Paragraph(
                f"{idx}. {path.get('name', '?')} — <b>{sev.upper()}</b>",
                ParagraphStyle(f"path_title_{idx}", fontSize=11, fontName="Helvetica-Bold",
                               textColor=BLACK, spaceAfter=4, spaceBefore=10),
            ))
            story.append(Paragraph(path.get("description", ""), styles["Normal"]))

            steps = path.get("steps", [])
            if steps:
                story.append(Paragraph("<b>Étapes d'exploitation :</b>",
                                       ParagraphStyle("steps_h", fontSize=9, fontName="Helvetica-Bold", spaceAfter=2)))
                for step in steps:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{step}",
                                           ParagraphStyle("step", fontSize=9, textColor=colors.HexColor("#333333"))))

            story.append(Paragraph(f"<b>Impact :</b> {path.get('impact', '—')}",
                                   ParagraphStyle("impact", fontSize=9, textColor=RED_MID, spaceBefore=4)))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e5e5")))

        # ── Recommendations ────────────────────────────────────────────────
        story.append(PageBreak())
        story.append(self._h1("Recommandations Prioritaires"))

        priority_recs = [
            ("Immédiat (J+0)", [
                "Désactiver tous les comptes admin dormants ou orphelins",
                "Supprimer les SPN des comptes admin (risque Kerberoasting)",
                "Patcher ou isoler les systèmes EOL identifiés",
            ]),
            ("Court terme (J+30)", [
                "Mettre en place une politique de mots de passe forte (≥16 car.)",
                "Activer la protection LAPS sur les postes de travail",
                "Réduire les membres des groupes Domain Admins / Enterprise Admins",
            ]),
            ("Moyen terme (J+90)", [
                "Déployer Microsoft Defender for Identity (MDI) pour la détection",
                "Mettre en place un Tier Model pour l'administration",
                "Activer l'audit des ACL et des modifications de groupes privilégiés",
            ]),
        ]

        for period, recs in priority_recs:
            story.append(Paragraph(period, ParagraphStyle("period", fontSize=11, fontName="Helvetica-Bold",
                                                          textColor=RED_MID, spaceBefore=10, spaceAfter=4)))
            for rec in recs:
                story.append(Paragraph(f"• {rec}", ParagraphStyle("rec_item", fontSize=9, leftIndent=12)))

        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph(
            "Rapport généré automatiquement par AD Recon & Attack Path Mapper",
            ParagraphStyle("footer", fontSize=8, textColor=colors.grey, alignment=TA_CENTER),
        ))

        doc.build(story)
        return filename

    def _h1(self, text: str) -> Paragraph:
        return Paragraph(
            text,
            ParagraphStyle("h1", fontSize=16, fontName="Helvetica-Bold",
                           textColor=RED_DARK, spaceBefore=16, spaceAfter=8,
                           borderPad=4),
        )
