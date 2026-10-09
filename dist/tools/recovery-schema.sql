CREATE TABLE `attachments` (
	`id` text PRIMARY KEY NOT NULL,
	`topic` text NOT NULL,
	`owner` text NOT NULL,
	`name` text NOT NULL,
	`mime` text NOT NULL,
	`size` integer NOT NULL,
	`storage_key` text NOT NULL,
	`visibility` text DEFAULT 'private' NOT NULL,
	`allow_export` integer DEFAULT 0 NOT NULL,
	`source` text DEFAULT '' NOT NULL,
	`status` text DEFAULT 'uploading' NOT NULL,
	`created` integer NOT NULL,
	FOREIGN KEY (`topic`) REFERENCES `topics`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`owner`) REFERENCES `profiles`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `attachments_topic` ON `attachments` (`topic`);--> statement-breakpoint
CREATE INDEX `attachments_owner` ON `attachments` (`owner`);--> statement-breakpoint
CREATE TABLE `audit` (
	`id` text PRIMARY KEY NOT NULL,
	`moderator` text NOT NULL,
	`target_type` text NOT NULL,
	`target_id` text NOT NULL,
	`action` text NOT NULL,
	`reason` text NOT NULL,
	`created` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `audit_target_created` ON `audit` (`target_type`,`target_id`,`created`);--> statement-breakpoint
CREATE TABLE `cases` (
	`id` text PRIMARY KEY NOT NULL,
	`user` text NOT NULL,
	`kind` text NOT NULL,
	`target_type` text NOT NULL,
	`target_id` text NOT NULL,
	`reason` text NOT NULL,
	`details` text NOT NULL,
	`status` text DEFAULT 'pending' NOT NULL,
	`decision` text DEFAULT '' NOT NULL,
	`created` integer NOT NULL,
	`updated` integer NOT NULL,
	FOREIGN KEY (`user`) REFERENCES `profiles`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `cases_status_created` ON `cases` (`status`,`created`);--> statement-breakpoint
CREATE INDEX `cases_user_created` ON `cases` (`user`,`created`);--> statement-breakpoint
CREATE TABLE `limits` (
	`key` text PRIMARY KEY NOT NULL,
	`window` integer NOT NULL,
	`count` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `notices` (
	`id` text PRIMARY KEY NOT NULL,
	`user` text NOT NULL,
	`topic` text,
	`message` text NOT NULL,
	`is_read` integer DEFAULT 0 NOT NULL,
	`created` integer NOT NULL,
	FOREIGN KEY (`user`) REFERENCES `profiles`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `notices_user_created` ON `notices` (`user`,`created`);--> statement-breakpoint
CREATE TABLE `profiles` (
	`id` text PRIMARY KEY NOT NULL,
	`public_id` text NOT NULL,
	`nickname` text NOT NULL,
	`accepted_rules` text DEFAULT '' NOT NULL,
	`approved_topics` integer DEFAULT 0 NOT NULL,
	`suspended_until` integer DEFAULT 0 NOT NULL,
	`created` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `profiles_public_id` ON `profiles` (`public_id`);--> statement-breakpoint
CREATE TABLE `replies` (
	`id` text PRIMARY KEY NOT NULL,
	`topic` text NOT NULL,
	`author` text NOT NULL,
	`parent` text,
	`body` text NOT NULL,
	`source` text DEFAULT '' NOT NULL,
	`status` text NOT NULL,
	`allow_export` integer DEFAULT 0 NOT NULL,
	`reason` text DEFAULT '' NOT NULL,
	`created` integer NOT NULL,
	`updated` integer NOT NULL,
	FOREIGN KEY (`topic`) REFERENCES `topics`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`author`) REFERENCES `profiles`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `replies_topic_status_created` ON `replies` (`topic`,`status`,`created`);--> statement-breakpoint
CREATE INDEX `replies_author_created` ON `replies` (`author`,`created`);--> statement-breakpoint
CREATE TABLE `subscriptions` (
	`id` text PRIMARY KEY NOT NULL,
	`user` text NOT NULL,
	`topic` text NOT NULL,
	FOREIGN KEY (`user`) REFERENCES `profiles`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`topic`) REFERENCES `topics`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `subscriptions_user_topic` ON `subscriptions` (`user`,`topic`);--> statement-breakpoint
CREATE INDEX `subscriptions_topic` ON `subscriptions` (`topic`);--> statement-breakpoint
CREATE TABLE `topics` (
	`id` text PRIMARY KEY NOT NULL,
	`author` text NOT NULL,
	`title` text NOT NULL,
	`body` text NOT NULL,
	`category` text NOT NULL,
	`region` text DEFAULT '' NOT NULL,
	`institution` text DEFAULT '' NOT NULL,
	`source` text DEFAULT '' NOT NULL,
	`status` text DEFAULT 'draft' NOT NULL,
	`progress` text DEFAULT 'open' NOT NULL,
	`allow_export` integer DEFAULT 0 NOT NULL,
	`sensitive` integer DEFAULT 0 NOT NULL,
	`reason` text DEFAULT '' NOT NULL,
	`slow_seconds` integer DEFAULT 0 NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`created` integer NOT NULL,
	`updated` integer NOT NULL,
	`published` integer,
	FOREIGN KEY (`author`) REFERENCES `profiles`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `topics_status_updated` ON `topics` (`status`,`updated`);--> statement-breakpoint
CREATE INDEX `topics_author_created` ON `topics` (`author`,`created`);
ALTER TABLE `attachments` ADD `consent_rules` text DEFAULT '' NOT NULL;
ALTER TABLE `topics` ADD `requires_review` integer DEFAULT 0 NOT NULL;
CREATE TABLE `archive_media` (
	`id` text PRIMARY KEY NOT NULL,
	`record` text NOT NULL,
	`file` text NOT NULL,
	FOREIGN KEY (`record`) REFERENCES `archive_records`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`file`) REFERENCES `intake_files`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `archive_media_record_file` ON `archive_media` (`record`,`file`);--> statement-breakpoint
CREATE TABLE `archive_records` (
	`id` text PRIMARY KEY NOT NULL,
	`intake` text NOT NULL,
	`name` text NOT NULL,
	`aliases` text DEFAULT '' NOT NULL,
	`region` text DEFAULT '' NOT NULL,
	`city` text DEFAULT '' NOT NULL,
	`summary` text NOT NULL,
	`body` text NOT NULL,
	`sources` text NOT NULL,
	`verification` text NOT NULL,
	`allow_export` integer DEFAULT 0 NOT NULL,
	`status` text DEFAULT 'published' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`created` integer NOT NULL,
	`updated` integer NOT NULL,
	FOREIGN KEY (`intake`) REFERENCES `intake`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `archive_status_updated` ON `archive_records` (`status`,`updated`);--> statement-breakpoint
CREATE TABLE `intake` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text DEFAULT '' NOT NULL,
	`receipt_hash` text NOT NULL,
	`kind` text NOT NULL,
	`title` text NOT NULL,
	`institution` text DEFAULT '' NOT NULL,
	`region` text DEFAULT '' NOT NULL,
	`body` text NOT NULL,
	`source_note` text DEFAULT '' NOT NULL,
	`scope` text DEFAULT 'review' NOT NULL,
	`rights` integer DEFAULT 0 NOT NULL,
	`allow_export` integer DEFAULT 0 NOT NULL,
	`status` text DEFAULT 'draft' NOT NULL,
	`decision` text DEFAULT '' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`created` integer NOT NULL,
	`updated` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `intake_status_updated` ON `intake` (`status`,`updated`);--> statement-breakpoint
CREATE INDEX `intake_owner_updated` ON `intake` (`owner`,`updated`);--> statement-breakpoint
CREATE TABLE `intake_events` (
	`id` text PRIMARY KEY NOT NULL,
	`intake` text NOT NULL,
	`action` text NOT NULL,
	`message` text NOT NULL,
	`created` integer NOT NULL,
	FOREIGN KEY (`intake`) REFERENCES `intake`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `intake_events_intake` ON `intake_events` (`intake`,`created`);--> statement-breakpoint
CREATE TABLE `intake_files` (
	`id` text PRIMARY KEY NOT NULL,
	`intake` text NOT NULL,
	`name` text NOT NULL,
	`mime` text NOT NULL,
	`size` integer NOT NULL,
	`storage_key` text NOT NULL,
	`sha256` text NOT NULL,
	`public_allowed` integer DEFAULT 0 NOT NULL,
	`export_allowed` integer DEFAULT 0 NOT NULL,
	`status` text DEFAULT 'ready' NOT NULL,
	`created` integer NOT NULL,
	FOREIGN KEY (`intake`) REFERENCES `intake`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `intake_files_intake` ON `intake_files` (`intake`);