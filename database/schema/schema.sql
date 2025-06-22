-- CreateTable
CREATE TABLE "user" (
    "id" TEXT NOT NULL PRIMARY KEY
);

-- CreateTable
CREATE TABLE "guild" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "prefix" TEXT NOT NULL,
    "r34_enabled" BOOLEAN NOT NULL DEFAULT false,
    "created_at" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "guild_user_profile" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "guild_id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL,
    CONSTRAINT "guild_user_profile_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "guild" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "guild_user_profile_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "user_command_count" (
    "user_id" TEXT NOT NULL PRIMARY KEY,
    "category" TEXT NOT NULL,
    "count" INTEGER NOT NULL,
    CONSTRAINT "user_command_count_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "guild_user_profile" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "r34_user_profile" (
    "user_id" TEXT NOT NULL PRIMARY KEY,
    "blacklist_enabled" BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT "r34_user_profile_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "guild_user_profile" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "r34_user_blacklist" (
    "user_id" TEXT NOT NULL,
    "term" TEXT NOT NULL,

    PRIMARY KEY ("user_id", "term"),
    CONSTRAINT "r34_user_blacklist_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "guild_user_profile" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "r34_user_bookmarks" (
    "user_id" TEXT NOT NULL,
    "post_id" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL,

    PRIMARY KEY ("user_id", "post_id"),
    CONSTRAINT "r34_user_bookmarks_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "guild_user_profile" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "guild_user_profile_guild_id_user_id_key" ON "guild_user_profile"("guild_id", "user_id");

