"""Tray transitions preserve settings and the independent host; no real accounts."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from desktop_window import MonitorWindow
import aim_control as control


class TrayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.window = MonitorWindow(Path(self.directory.name), monitor=False)
        self.window.show(); self.application.processEvents()
        self.window.tray = Mock(); self.window.tray.isVisible.return_value = True
        self.window.tray_start = Mock(); self.window.tray_stop = Mock(); self.window.tray_quit = Mock()
        available = patch.object(QSystemTrayIcon, 'isSystemTrayAvailable', return_value=True)
        available.start(); self.addCleanup(available.stop)
        hosts = patch.object(control, 'owned_hosts', return_value=[])
        hosts.start(); self.addCleanup(hosts.stop)
        self.addCleanup(self.cleanup_window)

    def cleanup_window(self):
        self.window.unsaved=False; self.window.quit_requested=True
        self.window.config['keep_host_on_close']=True
        self.window.close(); self.window.deleteLater()

    def test_minimize_preserves_unsaved_key_and_never_stops_host(self):
        self.window.key.setText('fixture-key'); self.window.unsaved=True
        with patch.object(control, 'stop_host') as stop:
            self.window.showMinimized(); self.application.processEvents(); self.application.processEvents()
        self.assertTrue(self.window.hidden_to_tray); self.assertFalse(self.window.isVisible())
        self.assertTrue(self.window.unsaved); self.assertEqual(self.window.key.text(), 'fixture-key')
        stop.assert_not_called()
        self.window.restore_from_tray()
        self.assertTrue(self.window.isVisible()); self.assertFalse(self.window.isMinimized())

    def test_close_to_tray_retains_unsaved_settings_without_a_quit_dialog(self):
        self.window.config['close_to_tray']=True; self.window.unsaved=True
        self.window.config['keep_host_on_close']=False
        with patch.object(QMessageBox,'question') as question, patch.object(control,'stop_host') as stop:
            event=QCloseEvent(); self.window.closeEvent(event)
        self.assertFalse(event.isAccepted()); self.assertTrue(self.window.hidden_to_tray)
        self.assertTrue(self.window.unsaved); question.assert_not_called(); stop.assert_not_called()

    def test_no_tray_leaves_normal_close_behavior_available(self):
        self.window.config['close_to_tray']=True
        with patch.object(QSystemTrayIcon,'isSystemTrayAvailable',return_value=False):
            self.assertFalse(self.window.hide_to_tray())
            event=QCloseEvent(); self.window.closeEvent(event)
        self.assertTrue(event.isAccepted())

    def test_quit_uses_stop_preference_instead_of_hiding(self):
        self.window.config.update(close_to_tray=True, keep_host_on_close=False)
        with patch.object(self.window,'_run') as run:
            self.window.request_quit()
        self.assertTrue(self.window.quit_requested); self.assertTrue(self.window.close_after_stop)
        self.assertEqual(run.call_args.args[0], 'Stopping host')
        self.window.close_after_stop=False

    def test_declined_unsaved_quit_resets_exit_intent(self):
        self.window.config['close_to_tray']=True; self.window.unsaved=True
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No):
            self.window.request_quit()
        self.assertFalse(self.window.quit_requested); self.assertTrue(self.window.isVisible())
        self.assertTrue(self.window.unsaved)

    def test_busy_quit_restores_progress_instead_of_exiting(self):
        self.window.hide_to_tray(); self.window.busy=True
        self.window.request_quit()
        self.assertTrue(self.window.isVisible()); self.assertFalse(self.window.quit_requested)
        self.assertTrue(self.window.busy)
        self.window.busy=False

    def test_hidden_action_error_reopens_the_window(self):
        self.window.hide_to_tray()
        with patch.object(QMessageBox,'warning') as warning:
            self.window._finished(False, 'Synthetic USB failure')
        self.assertTrue(self.window.isVisible()); warning.assert_called_once()

    def test_tray_tooltip_and_quit_menu_contain_no_saved_key(self):
        self.window.config['zai_key']='fixture-private-key'
        self.window.config['keep_host_on_close']=False
        self.window.refresh_tray()
        self.assertNotIn('fixture-private-key',str(self.window.tray.setToolTip.call_args))
        self.assertIn('stop host',self.window.tray_quit.setText.call_args.args[0])

    def test_tray_preferences_are_saved_and_reloaded(self):
        self.window.board.setCurrentIndex(self.window.board.findData('guition-p4'))
        self.window.providers['gemini'].setChecked(True)
        self.window.minimize_tray.setChecked(False); self.window.close_tray.setChecked(True)
        self.window.save()
        config=control.local_config(self.window.root)
        self.assertFalse(config['minimize_to_tray']); self.assertTrue(config['close_to_tray'])
        other=MonitorWindow(self.window.root,monitor=False)
        self.assertFalse(other.minimize_tray.isChecked()); self.assertTrue(other.close_tray.isChecked())
        other.quit_requested=True; other.close(); other.deleteLater()

    def test_restoring_retains_window_size_and_maximized_state(self):
        self.window.resize(1200, 900); self.application.processEvents()
        before=self.window.size()
        self.window.showMinimized(); self.application.processEvents(); self.application.processEvents()
        self.window.restore_from_tray(); self.application.processEvents()
        self.assertEqual(self.window.size(),before)
        self.window.showMaximized(); self.application.processEvents()
        self.window.hide_to_tray(); self.window.restore_from_tray()
        self.assertTrue(self.window.isMaximized())


if __name__=='__main__': unittest.main()
