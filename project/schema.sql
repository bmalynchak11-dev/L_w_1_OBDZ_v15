-- DDL Схема бази даних FinTrecker (PostgreSQL 18)

DROP TABLE IF EXISTS "transaction_tag" CASCADE;
DROP TABLE IF EXISTS "receipt_item" CASCADE;
DROP TABLE IF EXISTS "transaction" CASCADE;
DROP TABLE IF EXISTS "category" CASCADE;
DROP TABLE IF EXISTS "account" CASCADE;
DROP TABLE IF EXISTS "profile" CASCADE;
DROP TABLE IF EXISTS "tag" CASCADE;
DROP TABLE IF EXISTS "app_user" CASCADE;

-- 1. Таблиця app_user (сильна сутність зі складеним атрибутом)
CREATE TABLE "app_user" (
    "id" integer GENERATED ALWAYS AS IDENTITY,
    "email" text NOT NULL,
    "password_hash" text NOT NULL,
    "full_name_first_name" text NOT NULL,
    "full_name_last_name" text NOT NULL,
    CONSTRAINT "pk_app_user" PRIMARY KEY ("id"),
    CONSTRAINT "uk_app_user_email" UNIQUE ("email")
);

-- 2. Таблиця profile (зв'язок 1:1 з app_user)
CREATE TABLE "profile" (
    "id" integer GENERATED ALWAYS AS IDENTITY,
    "default_currency" text NOT NULL,
    "locale" text,
    "app_user_id" integer NOT NULL,
    CONSTRAINT "pk_profile" PRIMARY KEY ("id"),
    CONSTRAINT "uk_profile_app_user_id" UNIQUE ("app_user_id"),
    CONSTRAINT "fk_profile_app_user" FOREIGN KEY ("app_user_id") 
        REFERENCES "app_user" ("id") ON DELETE CASCADE
);

-- 3. Таблиця account (зв'язок 1:N з app_user)
CREATE TABLE "account" (
    "id" integer GENERATED ALWAYS AS IDENTITY,
    "name" text NOT NULL,
    "balance" numeric(12,2) NOT NULL DEFAULT 0.00,
    "app_user_id" integer NOT NULL,
    CONSTRAINT "pk_account" PRIMARY KEY ("id"),
    CONSTRAINT "fk_account_app_user" FOREIGN KEY ("app_user_id") 
        REFERENCES "app_user" ("id") ON DELETE RESTRICT
);

-- 4. Таблиця category
CREATE TABLE "category" (
    "id" integer GENERATED ALWAYS AS IDENTITY,
    "title" text NOT NULL,
    "kind" text NOT NULL,
    CONSTRAINT "pk_category" PRIMARY KEY ("id"),
    CONSTRAINT "chk_category_kind" CHECK ("kind" IN ('INCOME', 'EXPENSE'))
);

-- 5. Таблиця tag
CREATE TABLE "tag" (
    "id" integer GENERATED ALWAYS AS IDENTITY,
    "name" text NOT NULL,
    CONSTRAINT "pk_tag" PRIMARY KEY ("id"),
    CONSTRAINT "uk_tag_name" UNIQUE ("name")
);

-- 6. Таблиця transaction (зв'язок 1:N з account та category)
CREATE TABLE "transaction" (
    "id" integer GENERATED ALWAYS AS IDENTITY,
    "amount" numeric(12,2) NOT NULL,
    "transacted_at" timestamptz NOT NULL,
    "note" text,
    "account_id" integer NOT NULL,
    "category_id" integer,
    CONSTRAINT "pk_transaction" PRIMARY KEY ("id"),
    CONSTRAINT "chk_transaction_amount" CHECK ("amount" > 0),
    CONSTRAINT "fk_transaction_account" FOREIGN KEY ("account_id") 
        REFERENCES "account" ("id") ON DELETE CASCADE,
    CONSTRAINT "fk_transaction_category" FOREIGN KEY ("category_id") 
        REFERENCES "category" ("id") ON DELETE SET NULL
);

-- 7. Таблиця receipt_item (слабка сутність щодо transaction, складений PK)
CREATE TABLE "receipt_item" (
    "transaction_id" integer NOT NULL,
    "item_no" integer NOT NULL,
    "item_name" text NOT NULL,
    "price" numeric(12,2) NOT NULL,
    CONSTRAINT "pk_receipt_item" PRIMARY KEY ("transaction_id", "item_no"),
    CONSTRAINT "chk_receipt_item_price" CHECK ("price" >= 0),
    CONSTRAINT "fk_receipt_item_transaction" FOREIGN KEY ("transaction_id") 
        REFERENCES "transaction" ("id") ON DELETE CASCADE
);

-- 8. Таблиця transaction_tag (зв'язок M:N між transaction та tag)
CREATE TABLE "transaction_tag" (
    "transaction_id" integer NOT NULL,
    "tag_id" integer NOT NULL,
    CONSTRAINT "pk_transaction_tag" PRIMARY KEY ("transaction_id", "tag_id"),
    CONSTRAINT "fk_transaction_tag_tx" FOREIGN KEY ("transaction_id") 
        REFERENCES "transaction" ("id") ON DELETE CASCADE,
    CONSTRAINT "fk_transaction_tag_tag" FOREIGN KEY ("tag_id") 
        REFERENCES "tag" ("id") ON DELETE CASCADE
);