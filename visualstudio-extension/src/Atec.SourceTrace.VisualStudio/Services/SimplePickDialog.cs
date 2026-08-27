using System.Windows;
using System.Windows.Controls;

namespace Atec.SourceTrace.VisualStudio.Services;

public sealed class SimplePickDialog : Window
{
    private readonly ListBox _list;

    public int SelectedIndex { get; private set; } = -1;

    public SimplePickDialog(string title, string message, string[] items)
    {
        Title = title;
        Width = 480;
        Height = 360;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        ResizeMode = ResizeMode.CanResize;

        var root = new DockPanel { Margin = new Thickness(12) };
        var msg = new TextBlock
        {
            Text = message,
            TextWrapping = TextWrapping.Wrap,
            Margin = new Thickness(0, 0, 0, 8),
        };
        DockPanel.SetDock(msg, Dock.Top);
        root.Children.Add(msg);

        var buttons = new StackPanel
        {
            Orientation = Orientation.Horizontal,
            HorizontalAlignment = HorizontalAlignment.Right,
            Margin = new Thickness(0, 8, 0, 0),
        };
        DockPanel.SetDock(buttons, Dock.Bottom);

        var ok = new Button { Content = "확인", Width = 80, Margin = new Thickness(0, 0, 8, 0), IsDefault = true };
        var cancel = new Button { Content = "취소", Width = 80, IsCancel = true };
        ok.Click += (_, _) =>
        {
            SelectedIndex = _list.SelectedIndex;
            DialogResult = SelectedIndex >= 0;
            Close();
        };
        cancel.Click += (_, _) =>
        {
            DialogResult = false;
            Close();
        };
        buttons.Children.Add(ok);
        buttons.Children.Add(cancel);
        root.Children.Add(buttons);

        _list = new ListBox { ItemsSource = items, MinHeight = 180 };
        if (items.Length > 0)
        {
            _list.SelectedIndex = 0;
        }

        _list.MouseDoubleClick += (_, _) =>
        {
            SelectedIndex = _list.SelectedIndex;
            DialogResult = SelectedIndex >= 0;
            Close();
        };
        root.Children.Add(_list);

        Content = root;
    }
}
