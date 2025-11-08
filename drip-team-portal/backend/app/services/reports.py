from datetime import datetime
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.component import Component, ComponentStatus
from app.models.test import Test, TestResult, TestStatus
from app.models.audit import AuditLog

class ReportGenerator:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_validation_report(self, start_date: datetime, end_date: datetime) -> BytesIO:
        """Generate comprehensive validation report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12,
        )
        
        # Title
        title = Paragraph(
            f"DRIP System Validation Report<br/>"
            f"<font size=14>{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}</font>",
            title_style
        )
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        summary_data = self._get_summary_data(start_date, end_date)
        summary_text = self._format_summary(summary_data)
        story.append(Paragraph(summary_text, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
        
        # Component Status Section
        story.append(Paragraph("Component Status", heading_style))
        components_table = self._create_components_table()
        if components_table:
            story.append(components_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Test Results Section
        story.append(Paragraph("Test Results Summary", heading_style))
        test_results = self._create_test_results_section(start_date, end_date)
        story.extend(test_results)
        story.append(PageBreak())
        
        # Physics Validation Section
        story.append(Paragraph("Physics Validation", heading_style))
        physics_section = self._create_physics_validation_section()
        story.extend(physics_section)
        story.append(Spacer(1, 0.3*inch))
        
        # Risk Assessment
        story.append(Paragraph("Risk Assessment", heading_style))
        risks = self._create_risk_assessment()
        story.extend(risks)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_test_campaign_excel(self) -> BytesIO:
        """Generate Excel workbook with test campaign data"""
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Components sheet
            components_df = self._get_components_dataframe()
            components_df.to_excel(writer, sheet_name='Components', index=False)
            
            # Tests sheet
            tests_df = self._get_tests_dataframe()
            tests_df.to_excel(writer, sheet_name='Tests', index=False)
            
            # Results sheet
            results_df = self._get_results_dataframe()
            results_df.to_excel(writer, sheet_name='Results', index=False)
            
            # Physics validation sheet
            physics_df = self._get_physics_dataframe()
            physics_df.to_excel(writer, sheet_name='Physics', index=False)
            
            # Summary sheet
            summary_df = self._get_summary_dataframe()
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Format worksheets
            workbook = writer.book
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.autofilter(0, 0, 100, 20)  # Add autofilter
                
                # Auto-adjust column widths
                for i, col in enumerate(components_df.columns):
                    worksheet.set_column(i, i, 15)
        
        buffer.seek(0)
        return buffer
    
    def _get_summary_data(self, start_date: datetime, end_date: datetime) -> dict:
        """Get summary statistics for report"""
        total_components = self.db.query(Component).count()
        verified_components = self.db.query(Component).filter(
            Component.status == ComponentStatus.VERIFIED
        ).count()
        
        total_tests = self.db.query(Test).count()
        completed_tests = self.db.query(Test).filter(
            Test.status == TestStatus.COMPLETED,
            Test.executed_date >= start_date,
            Test.executed_date <= end_date
        ).count()
        
        physics_validated = self.db.query(TestResult).filter(
            TestResult.physics_validated == True
        ).count()
        
        return {
            "total_components": total_components,
            "verified_components": verified_components,
            "verification_rate": (verified_components / total_components * 100) if total_components > 0 else 0,
            "total_tests": total_tests,
            "completed_tests": completed_tests,
            "physics_validated": physics_validated,
            "period_days": (end_date - start_date).days
        }
    
    def _format_summary(self, data: dict) -> str:
        """Format summary data as text"""
        return (
            f"During the {data['period_days']}-day reporting period, "
            f"{data['completed_tests']} tests were completed out of {data['total_tests']} total tests. "
            f"Component verification stands at {data['verification_rate']:.1f}% "
            f"with {data['verified_components']} of {data['total_components']} components verified. "
            f"{data['physics_validated']} test results have been validated against DRIP physics models."
        )
    
    def _create_components_table(self) -> Table:
        """Create components status table"""
        # Get component summary by category and status
        components = self.db.query(
            Component.category,
            Component.status,
            func.count(Component.id).label('count')
        ).group_by(Component.category, Component.status).all()
        
        if not components:
            return None
        
        # Organize data
        categories = set(c.category for c in components)
        statuses = [s.value for s in ComponentStatus]
        
        # Build table data
        data = [['Category'] + statuses + ['Total']]
        
        for category in sorted(categories):
            row = [category.value]
            total = 0
            for status in ComponentStatus:
                count = next(
                    (c.count for c in components if c.category == category and c.status == status),
                    0
                )
                row.append(str(count))
                total += count
            row.append(str(total))
            data.append(row)
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        return table
    
    def _create_test_results_section(self, start_date: datetime, end_date: datetime) -> list:
        """Create test results section"""
        story = []
        styles = getSampleStyleSheet()
        
        # Get test results in period
        results = self.db.query(TestResult).join(Test).filter(
            TestResult.executed_at >= start_date,
            TestResult.executed_at <= end_date
        ).all()
        
        if not results:
            story.append(Paragraph("No test results found in this period.", styles['BodyText']))
            return story
        
        # Summary statistics
        pass_count = sum(1 for r in results if r.result.value == "PASS")
        fail_count = sum(1 for r in results if r.result.value == "FAIL")
        partial_count = sum(1 for r in results if r.result.value == "PARTIAL")
        
        summary = f"Total Results: {len(results)} | Pass: {pass_count} | Fail: {fail_count} | Partial: {partial_count}"
        story.append(Paragraph(summary, styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))
        
        # Recent test results table
        data = [['Test ID', 'Component', 'Result', 'Date', 'Engineer']]
        for result in results[:20]:  # Show latest 20
            data.append([
                result.test.test_id,
                result.component.component_id if result.component else 'N/A',
                result.result.value,
                result.executed_at.strftime('%Y-%m-%d'),
                result.executed_by.split('@')[0]  # Just username
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        
        return story
    
    def _create_physics_validation_section(self) -> list:
        """Create physics validation section"""
        story = []
        styles = getSampleStyleSheet()
        
        # Get results with DRIP numbers
        results_with_drip = self.db.query(TestResult).filter(
            TestResult.drip_number.isnot(None)
        ).all()
        
        if not results_with_drip:
            story.append(Paragraph("No DRIP validation data available.", styles['BodyText']))
            return story
        
        # Calculate statistics
        drip_numbers = [r.drip_number for r in results_with_drip]
        avg_drip = sum(drip_numbers) / len(drip_numbers)
        validated_count = sum(1 for r in results_with_drip if r.physics_validated)
        
        text = (
            f"DRIP Number Statistics:\n"
            f"- Average DRIP Number: {avg_drip:.3f}\n"
            f"- Range: {min(drip_numbers):.3f} - {max(drip_numbers):.3f}\n"
            f"- Validated Results: {validated_count} of {len(results_with_drip)} "
            f"({validated_count/len(results_with_drip)*100:.1f}%)"
        )
        
        story.append(Paragraph(text.replace('\n', '<br/>'), styles['BodyText']))
        
        return story
    
    def _create_risk_assessment(self) -> list:
        """Create risk assessment section"""
        story = []
        styles = getSampleStyleSheet()
        
        risks = []
        
        # Check component verification rate
        total = self.db.query(Component).count()
        verified = self.db.query(Component).filter(
            Component.status == ComponentStatus.VERIFIED
        ).count()
        
        if total > 0 and verified / total < 0.8:
            risks.append(
                f"• Component Verification: Only {verified/total*100:.0f}% verified "
                f"(Target: 80%)"
            )
        
        # Check failed components
        failed = self.db.query(Component).filter(
            Component.status == ComponentStatus.FAILED
        ).count()
        if failed > 0:
            risks.append(f"• Failed Components: {failed} components require replacement")
        
        # Check blocked tests
        blocked = self.db.query(Test).filter(
            Test.status == TestStatus.BLOCKED
        ).count()
        if blocked > 0:
            risks.append(f"• Test Progress: {blocked} tests are currently blocked")
        
        if risks:
            story.append(Paragraph("<br/>".join(risks), styles['BodyText']))
        else:
            story.append(Paragraph("No significant risks identified.", styles['BodyText']))
        
        return story
    
    def _get_components_dataframe(self) -> pd.DataFrame:
        """Get components data as DataFrame"""
        components = self.db.query(Component).all()
        
        data = []
        for comp in components:
            data.append({
                'Component ID': comp.component_id,
                'Name': comp.name,
                'Part Number': comp.part_number,
                'Category': comp.category.value,
                'Status': comp.status.value,
                'Unit Cost': comp.unit_cost,
                'Quantity': comp.quantity,
                'Supplier': comp.supplier,
                'Order Date': comp.order_date,
                'Expected Delivery': comp.expected_delivery,
                'Updated By': comp.updated_by,
                'Updated At': comp.updated_at
            })
        
        return pd.DataFrame(data)
    
    def _get_tests_dataframe(self) -> pd.DataFrame:
        """Get tests data as DataFrame"""
        tests = self.db.query(Test).all()
        
        data = []
        for test in tests:
            data.append({
                'Test ID': test.test_id,
                'Name': test.name,
                'Category': test.category,
                'Status': test.status.value,
                'Duration (hrs)': test.duration_hours,
                'Executed Date': test.executed_date,
                'Engineer': test.engineer,
                'Prerequisites': ', '.join(test.prerequisites) if test.prerequisites else '',
                'Linear Issue': test.linear_issue_id
            })
        
        return pd.DataFrame(data)
    
    def _get_results_dataframe(self) -> pd.DataFrame:
        """Get test results data as DataFrame"""
        results = self.db.query(TestResult).all()
        
        data = []
        for result in results:
            data.append({
                'Test ID': result.test.test_id if result.test else '',
                'Component ID': result.component.component_id if result.component else '',
                'Result': result.result.value,
                'Steering Force (μN)': result.steering_force,
                'Bonding Strength (MPa)': result.bonding_strength,
                'Max Temperature (°C)': result.temperature_max,
                'DRIP Number': result.drip_number,
                'Physics Validated': result.physics_validated,
                'Executed At': result.executed_at,
                'Executed By': result.executed_by
            })
        
        return pd.DataFrame(data)
    
    def _get_physics_dataframe(self) -> pd.DataFrame:
        """Get physics validation data as DataFrame"""
        results = self.db.query(TestResult).filter(
            TestResult.drip_number.isnot(None)
        ).all()
        
        data = []
        for result in results:
            data.append({
                'Test ID': result.test.test_id if result.test else '',
                'DRIP Number': result.drip_number,
                'Physics Validated': result.physics_validated,
                'Test Category': result.test.category if result.test else '',
                'Result': result.result.value,
                'Date': result.executed_at
            })
        
        return pd.DataFrame(data)
    
    def _get_summary_dataframe(self) -> pd.DataFrame:
        """Get summary statistics as DataFrame"""
        summary_data = []
        
        # Component summary
        for status in ComponentStatus:
            count = self.db.query(Component).filter(Component.status == status).count()
            summary_data.append({
                'Metric': f'Components - {status.value}',
                'Value': count
            })
        
        # Test summary
        for status in TestStatus:
            count = self.db.query(Test).filter(Test.status == status).count()
            summary_data.append({
                'Metric': f'Tests - {status.value}',
                'Value': count
            })
        
        # Physics validation
        physics_count = self.db.query(TestResult).filter(
            TestResult.physics_validated == True
        ).count()
        summary_data.append({
            'Metric': 'Physics Validated Results',
            'Value': physics_count
        })
        
        return pd.DataFrame(summary_data)