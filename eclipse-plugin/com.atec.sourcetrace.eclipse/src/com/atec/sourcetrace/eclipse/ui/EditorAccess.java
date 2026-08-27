package com.atec.sourcetrace.eclipse.ui;

import java.io.File;
import java.net.URI;

import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IFileEditorInput;
import org.eclipse.ui.IPathEditorInput;
import org.eclipse.ui.IURIEditorInput;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.texteditor.ITextEditor;

/**
 * Reads active text editor selection/cursor without modifying project files.
 */
public final class EditorAccess {

	public static final class Snapshot {
		public final String filePath;
		public final String[] lines;
		public final String selectedText;
		public final int startLine0;
		public final int endLine0;
		public final String cursorWord;
		public final String currentLineText;
		public final boolean hasSelection;

		public Snapshot(
				String filePath,
				String[] lines,
				String selectedText,
				int startLine0,
				int endLine0,
				String cursorWord,
				String currentLineText,
				boolean hasSelection) {
			this.filePath = filePath;
			this.lines = lines;
			this.selectedText = selectedText;
			this.startLine0 = startLine0;
			this.endLine0 = endLine0;
			this.cursorWord = cursorWord;
			this.currentLineText = currentLineText;
			this.hasSelection = hasSelection;
		}
	}

	private EditorAccess() {
	}

	public static ITextEditor activeTextEditor() {
		IEditorPart part = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage().getActiveEditor();
		if (part instanceof ITextEditor) {
			return (ITextEditor) part;
		}
		return null;
	}

	public static Snapshot capture(ITextEditor editor) throws Exception {
		IDocument doc = editor.getDocumentProvider().getDocument(editor.getEditorInput());
		if (doc == null) {
			throw new Exception("문서를 읽을 수 없습니다.");
		}
		String full = doc.get();
		String[] lines = full.split("\\r?\\n", -1);
		ISelection sel = editor.getSelectionProvider().getSelection();
		String selectedText = "";
		int startLine0 = 0;
		int endLine0 = 0;
		boolean hasSelection = false;
		if (sel instanceof ITextSelection) {
			ITextSelection ts = (ITextSelection) sel;
			selectedText = ts.getText() == null ? "" : ts.getText();
			startLine0 = Math.max(0, ts.getStartLine());
			endLine0 = Math.max(0, ts.getEndLine());
			hasSelection = selectedText.trim().length() > 0;
		}
		String currentLineText = startLine0 < lines.length ? lines[startLine0] : "";
		String cursorWord = extractWord(currentLineText, estimateColumn(doc, sel));
		String filePath = resolveFilePath(editor);
		return new Snapshot(filePath, lines, selectedText, startLine0, endLine0, cursorWord,
				currentLineText, hasSelection);
	}

	private static int estimateColumn(IDocument doc, ISelection sel) {
		try {
			if (sel instanceof ITextSelection) {
				int offset = ((ITextSelection) sel).getOffset();
				return offset - doc.getLineOffset(doc.getLineOfOffset(offset));
			}
		} catch (Exception ignored) {
			// ignore
		}
		return 0;
	}

	private static String extractWord(String line, int column) {
		if (line == null || line.isEmpty()) {
			return "";
		}
		int col = Math.min(Math.max(column, 0), line.length());
		int start = col;
		int end = col;
		while (start > 0 && isIdentChar(line.charAt(start - 1))) {
			start--;
		}
		while (end < line.length() && isIdentChar(line.charAt(end))) {
			end++;
		}
		if (start >= end) {
			return "";
		}
		return line.substring(start, end);
	}

	private static boolean isIdentChar(char c) {
		return Character.isLetterOrDigit(c) || c == '_';
	}

	private static String resolveFilePath(ITextEditor editor) {
		Object input = editor.getEditorInput();
		if (input instanceof IFileEditorInput) {
			return ((IFileEditorInput) input).getFile().getLocation().toOSString();
		}
		if (input instanceof IPathEditorInput) {
			return ((IPathEditorInput) input).getPath().toOSString();
		}
		if (input instanceof IURIEditorInput) {
			URI uri = ((IURIEditorInput) input).getURI();
			if (uri != null && "file".equalsIgnoreCase(uri.getScheme())) {
				return new File(uri).getAbsolutePath();
			}
		}
		return editor.getEditorInput().getName();
	}
}
