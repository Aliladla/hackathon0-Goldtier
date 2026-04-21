"""
Odoo client for Gold tier autonomous AI employee.

Provides Python interface to Odoo ERP system with:
- Invoice creation and management
- Payment recording
- Financial queries
- Bidirectional sync (vault ↔ Odoo)
- Error recovery integration
- Operation queuing for offline scenarios
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import odoorpc

# Import Gold tier error recovery
try:
    from utils.error_recovery import get_error_recovery, PermanentError
    GOLD_TIER_AVAILABLE = True
except ImportError:
    GOLD_TIER_AVAILABLE = False

logger = logging.getLogger(__name__)


class OdooClient:
    """Client for Odoo ERP integration."""

    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        password: str,
        vault_path: Optional[str] = None
    ):
        """
        Initialize Odoo client.

        Args:
            url: Odoo instance URL
            db: Database name
            username: Odoo username
            password: Odoo password
            vault_path: Path to vault for sync operations
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.vault_path = Path(vault_path) if vault_path else None
        self.odoo = None
        self.uid = None

        # Error recovery
        self.error_recovery = None
        if GOLD_TIER_AVAILABLE:
            try:
                self.error_recovery = get_error_recovery()
            except RuntimeError:
                logger.warning("Error recovery not initialized, using basic error handling")

        logger.info(f"OdooClient initialized for {url}")

    def connect(self) -> None:
        """
        Connect and authenticate with Odoo.

        Raises:
            Exception: If connection or authentication fails
        """
        try:
            # Parse URL
            if self.url.startswith('https://'):
                host = self.url.replace('https://', '')
                protocol = 'jsonrpc+ssl'
                port = 443
            elif self.url.startswith('http://'):
                host = self.url.replace('http://', '')
                protocol = 'jsonrpc'
                port = 8069
            else:
                host = self.url
                protocol = 'jsonrpc'
                port = 8069

            # Remove port from host if present
            if ':' in host:
                host, port_str = host.split(':')
                port = int(port_str)

            # Connect
            self.odoo = odoorpc.ODOO(host, protocol=protocol, port=port)
            self.odoo.login(self.db, self.username, self.password)
            self.uid = self.odoo.env.uid

            logger.info(f"Connected to Odoo as user {self.uid}")

        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            raise

    def _ensure_connected(self) -> None:
        """Ensure connection is established."""
        if not self.odoo or not self.uid:
            self.connect()

    def _execute_with_recovery(self, func, *args, **kwargs):
        """
        Execute function with error recovery.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        if self.error_recovery:
            return self.error_recovery.with_retry(func, *args, **kwargs)
        else:
            # Basic retry without error recovery
            return func(*args, **kwargs)

    def create_invoice(
        self,
        partner_name: str,
        partner_email: str,
        invoice_lines: List[Dict[str, Any]],
        payment_term_days: int = 30,
        date_invoice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create invoice in Odoo.

        Args:
            partner_name: Customer name
            partner_email: Customer email
            invoice_lines: List of invoice line items
                Each item: {description, quantity, unit_price, account_id?}
            payment_term_days: Payment terms in days
            date_invoice: Invoice date (YYYY-MM-DD)

        Returns:
            Created invoice details

        Raises:
            Exception: If invoice creation fails
        """
        def _create():
            self._ensure_connected()

            # Find or create partner
            Partner = self.odoo.env['res.partner']
            partner_ids = Partner.search([('name', '=', partner_name)])

            if partner_ids:
                partner_id = partner_ids[0]
            else:
                # Create new partner
                partner_id = Partner.create({
                    'name': partner_name,
                    'email': partner_email,
                    'customer_rank': 1,
                })
                logger.info(f"Created new partner: {partner_name} (ID: {partner_id})")

            # Find payment term
            PaymentTerm = self.odoo.env['account.payment.term']
            payment_term_ids = PaymentTerm.search([('name', 'ilike', f'{payment_term_days} days')])
            payment_term_id = payment_term_ids[0] if payment_term_ids else None

            # Prepare invoice lines
            lines = []
            for line in invoice_lines:
                lines.append((0, 0, {
                    'name': line['description'],
                    'quantity': line.get('quantity', 1),
                    'price_unit': line['unit_price'],
                    'account_id': line.get('account_id'),
                }))

            # Create invoice
            Invoice = self.odoo.env['account.move']
            invoice_id = Invoice.create({
                'partner_id': partner_id,
                'move_type': 'out_invoice',
                'invoice_date': date_invoice or datetime.now().strftime('%Y-%m-%d'),
                'invoice_payment_term_id': payment_term_id,
                'invoice_line_ids': lines,
            })

            # Read created invoice
            invoice = Invoice.browse(invoice_id)
            result = {
                'id': invoice.id,
                'name': invoice.name,
                'partner_name': invoice.partner_id.name,
                'amount_total': invoice.amount_total,
                'state': invoice.state,
                'invoice_date': str(invoice.invoice_date),
                'invoice_date_due': str(invoice.invoice_date_due) if invoice.invoice_date_due else None,
            }

            logger.info(f"Created invoice: {result['name']} for {partner_name} (${result['amount_total']})")
            return result

        try:
            return self._execute_with_recovery(_create)
        except Exception as e:
            # Queue operation if error recovery available
            if self.error_recovery:
                self.error_recovery.queue_operation({
                    'type': 'create_invoice',
                    'partner_name': partner_name,
                    'partner_email': partner_email,
                    'invoice_lines': invoice_lines,
                    'payment_term_days': payment_term_days,
                    'date_invoice': date_invoice,
                })
                logger.warning(f"Invoice creation queued due to error: {e}")
            raise

    def record_payment(
        self,
        invoice_number: str,
        amount: float,
        payment_date: Optional[str] = None,
        payment_method: str = 'manual',
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record payment for an invoice.

        Args:
            invoice_number: Invoice number (e.g., INV/2026/0001)
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            payment_method: Payment method
            memo: Payment memo/reference

        Returns:
            Recorded payment details

        Raises:
            Exception: If payment recording fails
        """
        def _record():
            self._ensure_connected()

            # Find invoice
            Invoice = self.odoo.env['account.move']
            invoice_ids = Invoice.search([
                ('name', '=', invoice_number),
                ('move_type', '=', 'out_invoice')
            ])

            if not invoice_ids:
                raise ValueError(f"Invoice {invoice_number} not found")

            invoice_id = invoice_ids[0]
            invoice = Invoice.browse(invoice_id)

            # Find payment journal
            Journal = self.odoo.env['account.journal']
            journal_ids = Journal.search([('type', 'in', ['bank', 'cash'])])

            if not journal_ids:
                raise ValueError("No payment journal found")

            # Create payment
            Payment = self.odoo.env['account.payment']
            payment_id = Payment.create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': amount,
                'date': payment_date or datetime.now().strftime('%Y-%m-%d'),
                'journal_id': journal_ids[0],
                'ref': memo or f'Payment for {invoice_number}',
            })

            # Post payment
            payment = Payment.browse(payment_id)
            payment.action_post()

            # Reconcile with invoice
            payment_move = payment.move_id
            payment_lines = payment_move.line_ids.filtered(
                lambda l: l.account_id.internal_type == 'receivable'
            )
            invoice_lines = invoice.line_ids.filtered(
                lambda l: l.account_id.internal_type == 'receivable'
            )

            if payment_lines and invoice_lines:
                (payment_lines + invoice_lines).reconcile()

            result = {
                'id': payment.id,
                'name': payment.name,
                'amount': payment.amount,
                'date': str(payment.date),
                'state': payment.state,
                'invoice_number': invoice_number,
            }

            logger.info(f"Recorded payment: {result['name']} for {invoice_number} (${amount})")
            return result

        try:
            return self._execute_with_recovery(_record)
        except Exception as e:
            # Queue operation if error recovery available
            if self.error_recovery:
                self.error_recovery.queue_operation({
                    'type': 'record_payment',
                    'invoice_number': invoice_number,
                    'amount': amount,
                    'payment_date': payment_date,
                    'payment_method': payment_method,
                    'memo': memo,
                })
                logger.warning(f"Payment recording queued due to error: {e}")
            raise

    def query_financials(
        self,
        report_type: str = 'summary',
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        partner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query financial data from Odoo.

        Args:
            report_type: Type of report (summary, invoices, payments)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            partner_id: Filter by partner ID

        Returns:
            Financial data

        Raises:
            Exception: If query fails
        """
        def _query():
            self._ensure_connected()

            domain = []
            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to))
            if partner_id:
                domain.append(('partner_id', '=', partner_id))

            if report_type == 'invoices':
                # Query invoices
                Invoice = self.odoo.env['account.move']
                invoices = Invoice.search_read(
                    domain + [('move_type', '=', 'out_invoice')],
                    ['name', 'partner_id', 'invoice_date', 'amount_total', 'state', 'payment_state']
                )

                return {
                    'report_type': 'invoices',
                    'count': len(invoices),
                    'total_amount': sum(inv['amount_total'] for inv in invoices),
                    'invoices': invoices,
                }

            elif report_type == 'payments':
                # Query payments
                Payment = self.odoo.env['account.payment']
                payments = Payment.search_read(
                    domain + [('payment_type', '=', 'inbound')],
                    ['name', 'partner_id', 'date', 'amount', 'state']
                )

                return {
                    'report_type': 'payments',
                    'count': len(payments),
                    'total_amount': sum(pay['amount'] for pay in payments),
                    'payments': payments,
                }

            else:
                # Summary report
                Invoice = self.odoo.env['account.move']
                invoices = Invoice.search_read(
                    domain + [('move_type', '=', 'out_invoice')],
                    ['amount_total', 'state', 'payment_state']
                )

                Payment = self.odoo.env['account.payment']
                payments = Payment.search_read(
                    domain + [('payment_type', '=', 'inbound')],
                    ['amount']
                )

                return {
                    'report_type': 'summary',
                    'period': {'date_from': date_from, 'date_to': date_to},
                    'invoices': {
                        'count': len(invoices),
                        'total': sum(inv['amount_total'] for inv in invoices),
                        'paid': len([inv for inv in invoices if inv['payment_state'] == 'paid']),
                        'unpaid': len([inv for inv in invoices if inv['payment_state'] != 'paid']),
                    },
                    'payments': {
                        'count': len(payments),
                        'total': sum(pay['amount'] for pay in payments),
                    },
                }

        return self._execute_with_recovery(_query)

    def sync_from_odoo(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync data from Odoo to vault.

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            Sync results

        Raises:
            Exception: If sync fails
        """
        if not self.vault_path:
            raise ValueError("Vault path not configured")

        def _sync():
            self._ensure_connected()

            results = {
                'direction': 'from_odoo',
                'synced_invoices': 0,
                'synced_payments': 0,
                'errors': [],
            }

            # Sync invoices
            try:
                domain = []
                if date_from:
                    domain.append(('invoice_date', '>=', date_from))
                if date_to:
                    domain.append(('invoice_date', '<=', date_to))

                Invoice = self.odoo.env['account.move']
                invoices = Invoice.search_read(
                    domain + [('move_type', '=', 'out_invoice')],
                    ['name', 'partner_id', 'invoice_date', 'amount_total', 'state', 'payment_state']
                )

                # Write invoices to vault
                invoice_dir = self.vault_path / 'Accounting' / 'Invoices'
                invoice_dir.mkdir(parents=True, exist_ok=True)

                for invoice in invoices:
                    invoice_file = invoice_dir / f"{invoice['name'].replace('/', '_')}.json"
                    with open(invoice_file, 'w') as f:
                        json.dump(invoice, f, indent=2)

                results['synced_invoices'] = len(invoices)
                logger.info(f"Synced {len(invoices)} invoices from Odoo to vault")

            except Exception as e:
                results['errors'].append(f"Invoice sync error: {str(e)}")
                logger.error(f"Failed to sync invoices: {e}")

            return results

        return self._execute_with_recovery(_sync)

    def sync_to_odoo(self) -> Dict[str, Any]:
        """
        Sync data from vault to Odoo.

        Returns:
            Sync results

        Raises:
            Exception: If sync fails
        """
        if not self.vault_path:
            raise ValueError("Vault path not configured")

        def _sync():
            results = {
                'direction': 'to_odoo',
                'synced_invoices': 0,
                'synced_payments': 0,
                'errors': [],
            }

            # Process queued operations
            if self.error_recovery:
                queued_ops = self.error_recovery.get_queued_operations()

                for op in queued_ops:
                    try:
                        if op['type'] == 'create_invoice':
                            self.create_invoice(
                                op['partner_name'],
                                op['partner_email'],
                                op['invoice_lines'],
                                op.get('payment_term_days', 30),
                                op.get('date_invoice')
                            )
                            self.error_recovery.remove_queued_operation(op)
                            results['synced_invoices'] += 1

                        elif op['type'] == 'record_payment':
                            self.record_payment(
                                op['invoice_number'],
                                op['amount'],
                                op.get('payment_date'),
                                op.get('payment_method', 'manual'),
                                op.get('memo')
                            )
                            self.error_recovery.remove_queued_operation(op)
                            results['synced_payments'] += 1

                    except Exception as e:
                        results['errors'].append(f"Operation {op['type']} failed: {str(e)}")
                        logger.error(f"Failed to process queued operation: {e}")

            return results

        return self._execute_with_recovery(_sync)

    def bidirectional_sync(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform bidirectional sync between vault and Odoo.

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            Combined sync results
        """
        results = {
            'direction': 'bidirectional',
            'from_odoo': {},
            'to_odoo': {},
        }

        # Sync from Odoo to vault
        try:
            results['from_odoo'] = self.sync_from_odoo(date_from, date_to)
        except Exception as e:
            results['from_odoo'] = {'error': str(e)}
            logger.error(f"Failed to sync from Odoo: {e}")

        # Sync from vault to Odoo
        try:
            results['to_odoo'] = self.sync_to_odoo()
        except Exception as e:
            results['to_odoo'] = {'error': str(e)}
            logger.error(f"Failed to sync to Odoo: {e}")

        return results


def create_odoo_client(vault_path: Optional[str] = None) -> Optional[OdooClient]:
    """
    Create Odoo client from environment variables.

    Args:
        vault_path: Path to vault for sync operations

    Returns:
        OdooClient instance or None if not configured
    """
    url = os.getenv('ODOO_URL')
    db = os.getenv('ODOO_DB')
    username = os.getenv('ODOO_USERNAME')
    password = os.getenv('ODOO_PASSWORD')

    if not all([url, db, username, password]):
        logger.warning("Odoo not configured (missing environment variables)")
        return None

    return OdooClient(url, db, username, password, vault_path)
