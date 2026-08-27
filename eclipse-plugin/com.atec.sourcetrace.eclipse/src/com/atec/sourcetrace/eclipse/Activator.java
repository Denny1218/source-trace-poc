package com.atec.sourcetrace.eclipse;

import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.ui.plugin.AbstractUIPlugin;
import org.osgi.framework.BundleContext;

/**
 * Source Trace Eclipse Plug-in activator. Preferences only — does not touch
 * CDT project files (.project / .cproject / .settings).
 */
public class Activator extends AbstractUIPlugin {

	public static final String PLUGIN_ID = "com.atec.sourcetrace.eclipse";

	private static Activator plugin;

	@Override
	public void start(BundleContext context) throws Exception {
		super.start(context);
		plugin = this;
	}

	@Override
	public void stop(BundleContext context) throws Exception {
		plugin = null;
		super.stop(context);
	}

	public static Activator getDefault() {
		return plugin;
	}

	public static ImageDescriptor getImageDescriptor(String path) {
		return imageDescriptorFromPlugin(PLUGIN_ID, path);
	}
}
