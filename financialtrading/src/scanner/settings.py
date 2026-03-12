from PySide6.QtCore import QSettings


class Settings(QSettings):
    def __init__(self, bundle_identifier, app_name):
        super(Settings, self).__init__(
            QSettings.IniFormat, 
            QSettings.UserScope, 
            bundle_identifier, 
            app_name,
        )
        self._bundle_identifier = bundle_identifier
        self._app_name = app_name

    def bundle_identifier(self):
        return self._bundle_identifier
    
    def app_name(self):
        return self._app_name

    def _prepend_bundle_identifier_and_name(self, name):
        return '{}.{}.{}'.format(self._bundle_identifier, self._app_name, name)

    def get(self, name, default=None):
        if not name.startswith(self._bundle_identifier):
            name = self._prepend_bundle_identifier_and_name(name)
        value = self.value(name)
        if value is None or value == '':
            return default
        return value
    
    def get_int(self, name, default=None):
        try:
            return int(self.get(name, default))
        except ValueError as e:
            return default
        
    def get_float(self, name, default=None):
        try:
            return float(self.get(name, default))
        except ValueError as e:
            return default
        
    def get_bool(self, name, default=None):
        try:
            value = self.get(name, default)
            if value and isinstance(value, str):
                if value == '0' or value.lower() == 'false':
                    return False
                elif value == '1' or value.lower() == 'true':
                    return True
                else:
                    return default
            if value and isinstance(value, bool):
                return value
        except ValueError as e:
            return default
    
    def set(self, name, value):
        name = self._prepend_bundle_identifier_and_name(name)
        self.setValue(name, value)

    def to_string(self):
        text = f'Settings path: {self.fileName()}'
        for key in self.allKeys():
            text += f'\nSettings: {key}'
        return text