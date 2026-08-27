package com.atec.sourcetrace.eclipse.ui;

import org.eclipse.swt.SWT;
import org.eclipse.swt.browser.Browser;
import org.eclipse.swt.layout.FillLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.part.ViewPart;

import com.atec.sourcetrace.eclipse.core.MarkdownHtml;

/**
 * Displays Backend Markdown ({@code content}) without reinterpreting facts.
 */
public class ResultView extends ViewPart {

	public static final String ID = "com.atec.sourcetrace.eclipse.ui.ResultView";

	private Browser browser;

	@Override
	public void createPartControl(Composite parent) {
		parent.setLayout(new FillLayout());
		browser = new Browser(parent, SWT.NONE);
		browser.setText(MarkdownHtml.toHtmlDocument(
				"# ATEC Source Trace\n\n조회 결과가 여기에 표시됩니다.",
				"ATEC Source Trace"));
	}

	@Override
	public void setFocus() {
		if (browser != null && !browser.isDisposed()) {
			browser.setFocus();
		}
	}

	public void showMarkdown(String markdown, String title) {
		if (browser == null || browser.isDisposed()) {
			return;
		}
		browser.setText(MarkdownHtml.toHtmlDocument(markdown, title));
		setPartName(title == null || title.isEmpty() ? "ATEC Source Trace" : title);
	}
}
