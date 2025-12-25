-- Создание схемы admin_public
CREATE SCHEMA IF NOT EXISTS admin_public;

-- Предоставление прав доступа
GRANT USAGE ON SCHEMA admin_public TO ${DB_USER};
GRANT CREATE ON SCHEMA admin_public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA admin_public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA admin_public TO ${DB_USER};

-- Установка search_path по умолчанию для admin сервиса
ALTER ROLE ${DB_USER} SET search_path TO admin_public,public;
